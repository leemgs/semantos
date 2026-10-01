"""Experimental graph/RAG reasoner. Scores are heuristics, not probabilities.
No trained checkpoint or performance claim is supplied. Runtime is dry-run only.
"""
import os
import json
import statistics
import hashlib
from collections import Counter

import httpx
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse

KB_URL = os.environ.get("KB_URL", "http://kb-service:8000")
TELEMETRY_URL = os.environ.get("TELEMETRY_URL", "http://telemetry-agent:8000")
SAFETY_URL = os.environ.get("SAFETY_URL", "http://safety-runtime:8000")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "")
SELF_CONSISTENCY_K = int(os.environ.get("SELF_CONSISTENCY_K", "3"))

app = FastAPI(title="reasoner", version="1.0.0")

SYSTEM_PROMPT = """You are SemantOS Reasoner.
Generate guarded, explainable Linux kernel tuning recommendations from the
provided telemetry, retrieved traces, and the TYPED dependency neighborhood.
Rules:
- Return exactly one bundle, using the same bundle identifier for every member.
- Allowed controls: vm.swappiness, vm.dirty_ratio, vm.dirty_background_ratio.
- If changing either dirty ratio include both, with background < foreground.
- Prefer co-tuning knobs joined by a SYNERGIZES_WITH edge in the same bundle.
- Never co-propose two knobs joined by a CONFLICTS_WITH edge.
- Respect DEPENDS_ON ordering (tune the prerequisite first).
Return a single JSON object with key "recommendations": a list. Each item MUST
include: id, knob, proposed, rationale, expected_impact, uncertainty (0..1),
bundle (string tag grouping co-tuned knobs), explanation (2-4 sentences citing
telemetry stats and KB edges; no markdown). Strictly parseable JSON only."""

# Candidate knobs the reasoner considers (seed set; the KB expands via edges).
CANDIDATE_KNOBS = ["vm.dirty_ratio", "vm.dirty_background_ratio", "vm.swappiness"]


async def fetch_json(client, method, url, **kwargs):
    r = await client.request(method, url, **kwargs)
    r.raise_for_status()
    return r.json()


async def typed_neighborhood(client, knob):
    try:
        r = await client.get(f"{KB_URL}/kb/typed_neighborhood",
                             params={"knob": knob, "decayed": True})
        r.raise_for_status()
        return r.json().get("edges", [])
    except Exception:
        return []


async def rag_context():
    """Assemble telemetry + typed graph + retrieved traces."""
    async with httpx.AsyncClient(timeout=15) as client:
        tele = await fetch_json(client, "GET", f"{TELEMETRY_URL}/snapshot")
        m = tele["metrics"]
        q = (f"p95:{m.get('p95_latency_ms',0):.1f} "
             f"anomaly:{m.get('anomaly_rate',0):.3f} "
             f"load:{m.get('cpu_load_1',0):.2f}")
        nn = await fetch_json(client, "POST", f"{KB_URL}/kb/nn_search",
                              json={"query": q, "k": 5})
        graph = {}
        for knob in CANDIDATE_KNOBS:
            edges = await typed_neighborhood(client, knob)
            if edges:
                graph[knob] = edges
    return {"telemetry": tele, "retrieved_traces": nn.get("items", []),
            "dependency_graph": graph}


# --------------------------------------------------------------------------- #
# Model back-ends.  Each returns a dict with "recommendations".
# --------------------------------------------------------------------------- #
async def call_openai(prompt: str, temperature: float):
    async with httpx.AsyncClient(timeout=45) as client:
        r = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"model": OPENAI_MODEL, "temperature": temperature,
                  "response_format": {"type": "json_object"},
                  "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                               {"role": "user", "content": prompt}]})
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
    try:
        return json.loads(content)
    except Exception:
        return {"recommendations": []}


async def call_ollama(prompt: str, temperature: float):
    if not OLLAMA_MODEL:
        raise RuntimeError("Set OLLAMA_MODEL to an installed model with a recorded digest")
    async with httpx.AsyncClient(timeout=90) as client:
        r = await client.post(
            f"{OLLAMA_HOST}/api/generate",
            json={"model": OLLAMA_MODEL, "format": "json", "stream": False,
                  "options": {"temperature": temperature},
                  "prompt": SYSTEM_PROMPT + "\n" + prompt})
        r.raise_for_status()
        data = r.json()
    try:
        return json.loads(data.get("response", "{}"))
    except Exception:
        return {"recommendations": []}


async def sample_model(prompt: str, temperature: float):
    attempts = []
    if OPENAI_API_KEY:
        try:
            result = await call_openai(prompt, temperature)
            return {**result, 'backend_attempts': [{'backend': 'openai', 'status': 'returned'}]}
        except Exception as exc:
            attempts.append({'backend': 'openai', 'status': 'failed', 'error_type': type(exc).__name__})
    try:
        result = await call_ollama(prompt, temperature)
        return {**result, 'backend_attempts': attempts + [{'backend': 'ollama', 'status': 'returned'}]}
    except Exception as exc:
        attempts.append({'backend': 'ollama', 'status': 'failed', 'error_type': type(exc).__name__})
        return {'recommendations': [], 'backend_attempts': attempts}


# --------------------------------------------------------------------------- #
# Graph-grounded fallback: propose synergistic bundles directly from KB edges.
# --------------------------------------------------------------------------- #
def graph_grounded_fallback(ctx):
    # Without a model and validated empirical evidence, abstain. An invented
    # scheduler knob or an arbitrary value is not a defensible fallback.
    return {"recommendations": [], "reason": "no_validated_model_or_policy"}


# --------------------------------------------------------------------------- #
# Self-consistency aggregation over k samples.
# --------------------------------------------------------------------------- #
def _key(rec):
    return (str(rec.get("knob", "")).strip(), str(rec.get("proposed", "")).strip())


def aggregate_self_consistency(samples, ctx):
    """Merge k model samples; per-knob uncertainty = 1 - vote_fraction blended
    with KB edge-weight confidence."""
    votes = Counter()
    exemplar = {}
    for s in samples:
        if not s:
            continue
        seen = set()
        for rec in s.get("recommendations", []):
            k = _key(rec)
            if not k[0] or k in seen:
                continue
            seen.add(k)
            votes[k] += 1
            exemplar.setdefault(k, rec)

    k = max(1, len(samples))  # failed calls must not inflate agreement
    graph = ctx.get("dependency_graph", {})
    out = []
    chosen_knobs = set()
    # Select an actually proposed complete bundle; never splice incompatible
    # members from different samples into a new, unobserved combination.
    bundles = Counter()
    bundle_examples = {}
    for sample in samples:
        if not sample:
            continue
        recs = sample.get('recommendations', [])
        if not recs or len({_key(r)[0] for r in recs}) != len(recs):
            continue
        if len({r.get('bundle', '') for r in recs}) != 1:
            continue
        signature = tuple(sorted(_key(r) for r in recs))
        bundles[signature] += 1
        bundle_examples.setdefault(signature, recs)
    if not bundles:
        return {'recommendations': [], 'reason': 'no_coherent_bundle'}
    signature = bundles.most_common(1)[0][0]
    chosen = {_key(r): r for r in bundle_examples[signature]}
    for key, count in votes.most_common():
        if key not in chosen:
            continue
        if key[0] in chosen_knobs:
            continue
        chosen_knobs.add(key[0])
        rec = dict(chosen[key])
        agreement = count / k
        # KB confidence: strongest synergizing edge weight for this knob
        edges = graph.get(key[0], [])
        kb_conf = max([e["weight"] for e in edges
                       if e["edge_type"] == "synergizes_with"] or [0.0])
        # uncertainty: high when models disagree and KB evidence is weak
        u = (1.0 - agreement) * 0.7 + (1.0 - kb_conf) * 0.3
        rec["uncertainty"] = round(min(1.0, max(0.02, u)), 3)
        rec["provenance"] = {
            "score_kind": "heuristic_not_calibrated_probability",
            "self_consistency": {"votes": count, "k": k,
                                 "agreement": round(agreement, 3)},
            "kb_neighbors": edges[:4],
            "retrieved_traces": [t["text"] for t in ctx.get("retrieved_traces", [])[:3]],
            "telemetry_cue": {
                "p95_latency_ms": ctx["telemetry"]["metrics"].get("p95_latency_ms"),
                "anomaly_rate": ctx["telemetry"]["metrics"].get("anomaly_rate"),
            },
        }
        rec.setdefault("explanation",
                       f"Proposed by {count}/{k} samples; grounded on "
                       f"{len(edges)} typed KB edges.")
        out.append(rec)
    return {"recommendations": out}


@app.get("/healthz")
def healthz():
    return {"ok": True, "self_consistency_k": SELF_CONSISTENCY_K}


async def _recommend():
    """Core of the reasoning step: telemetry+KB retrieval -> k self-consistency
    samples -> aggregated, uncertainty-tagged recommendations. Returns a dict so
    both /get_recommendations and /apply can reuse it."""
    ctx = await rag_context()
    if not ctx["telemetry"].get("end_to_end_latency_valid", False):
        return {"recommendations": [], "reason": "measured_workload_telemetry_required"}
    # Preserve complete evidence and its identifiers in the decision record.
    prompt = json.dumps(ctx, sort_keys=True)
    if len(prompt) > 12000:
        return {'recommendations': [], 'reason': 'context_budget_exceeded'}

    samples = []
    for i in range(SELF_CONSISTENCY_K):
        temp = 0.2 + 0.3 * i          # spread temperatures for diversity
        s = await sample_model(prompt, temp)
        samples.append(s)

    result = aggregate_self_consistency(samples, ctx)
    result['decision_trace'] = {
        'context': ctx, 'system_prompt': SYSTEM_PROMPT, 'prompt': prompt,
        'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
        'samples': samples, 'sample_count': SELF_CONSISTENCY_K,
        'model_configuration': {'openai': OPENAI_MODEL if OPENAI_API_KEY else None,
                                'ollama': OLLAMA_MODEL or None},
        'scope': 'model proposals only; model digest and independent outcome still required',
    }
    return result


@app.post("/get_recommendations")
async def get_recommendations():
    return JSONResponse(await _recommend())


@app.post("/apply")
async def apply(body: dict = Body(default=None)):
    """Forward one complete bundle to the dry-run gate.

    This proxy performs no kernel writes, traffic staging or automatic rollback.
    An absent recommendations field requests fresh proposals; an empty list does not.
    """
    recs = (body or {}).get("recommendations")
    if recs is None:
        recs = (await _recommend()).get("recommendations", [])
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{SAFETY_URL}/apply",
                              json={"recommendations": recs})
        r.raise_for_status()
        result = r.json()
    return JSONResponse({"forwarded_to": "safety-runtime",
                         "submitted": len(recs), **result})


@app.post("/log_outcome")
async def log_outcome(context: dict = Body(...), action: dict = Body(...),
                      outcome: dict = Body(...)):
    """Persist an applied recommendation's realized outcome back into the KB so
    the dependency graph and RAG index learn from deployment."""
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(f"{KB_URL}/kb/upsert_trace",
                          json={"context": context, "action": action,
                                "outcome": outcome})
        response.raise_for_status()
    return {"ok": True}
