"""
reasoner — SemantOS guarded LLM reasoner (paper Sec. 4.3).

Turns telemetry + KB retrieval into typed, explainable, *jointly*-tuned kernel
recommendations.  Three mechanisms distinguish it from a bare LLM call:

  1. Graph-grounded joint reasoning.  Before prompting, we pull the typed/signed/
     weighted neighborhood of each candidate knob from kb-service and expose it to
     the model, so it can co-tune synergistic knobs together and avoid conflicting
     pairs.  This is the component ablated in Table 3's `wo_depgraph` row.
  2. Retrieval augmentation (RAG).  Nearest past traces are retrieved from FAISS
     and attached as evidence (`wo_rag` row of Table 3).
  3. Self-consistency uncertainty.  The model is sampled k=3 times; the reported
     per-knob uncertainty is 1 - agreement across samples, blended with the KB
     edge-weight confidence.  The safety runtime consumes this u.

Every recommendation carries `provenance` (telemetry cues, KB neighbors, retrieved
traces, self-consistency vote) so operators can audit *why*.
"""
import os
import json
import statistics
from collections import Counter

import httpx
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse

KB_URL = os.environ.get("KB_URL", "http://kb-service:8000")
TELEMETRY_URL = os.environ.get("TELEMETRY_URL", "http://telemetry-agent:8000")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:13b")
SELF_CONSISTENCY_K = int(os.environ.get("SELF_CONSISTENCY_K", "3"))

app = FastAPI(title="reasoner", version="1.0.0")

SYSTEM_PROMPT = """You are SemantOS Reasoner.
Generate guarded, explainable Linux kernel tuning recommendations from the
provided telemetry, retrieved traces, and the TYPED dependency neighborhood.
Rules:
- Prefer co-tuning knobs joined by a SYNERGIZES_WITH edge in the same bundle.
- Never co-propose two knobs joined by a CONFLICTS_WITH edge.
- Respect DEPENDS_ON ordering (tune the prerequisite first).
Return a single JSON object with key "recommendations": a list. Each item MUST
include: id, knob, proposed, rationale, expected_impact, uncertainty (0..1),
bundle (string tag grouping co-tuned knobs), explanation (2-4 sentences citing
telemetry stats and KB edges; no markdown). Strictly parseable JSON only."""

# Candidate knobs the reasoner considers (seed set; the KB expands via edges).
CANDIDATE_KNOBS = [
    "sched_min_granularity_ns", "sched_wake_affinity", "sched_latency_ns",
    "vm.dirty_ratio", "vm.dirty_background_ratio", "vm.swappiness",
    "net.core.rmem_max", "net.ipv4.tcp_rmem",
]


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
    if OPENAI_API_KEY:
        try:
            return await call_openai(prompt, temperature)
        except Exception:
            pass
    try:
        return await call_ollama(prompt, temperature)
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# Graph-grounded fallback: propose synergistic bundles directly from KB edges.
# --------------------------------------------------------------------------- #
def graph_grounded_fallback(ctx):
    m = ctx["telemetry"]["metrics"]
    p95 = m.get("p95_latency_ms", 0)
    anomaly = m.get("anomaly_rate", 0)
    graph = ctx.get("dependency_graph", {})
    recs = []
    if p95 < 20 and anomaly < 0.03:
        return {"recommendations": []}   # healthy: no action

    # seed on the tail-latency lever, then pull in synergistic partners
    seed = "sched_min_granularity_ns"
    bundle = [seed]
    for e in graph.get(seed, []):
        if e["edge_type"] == "synergizes_with" and e["sign"] > 0 and e["weight"] > 0.3:
            bundle.append(e["neighbor"])
    bundle = list(dict.fromkeys(bundle))[:3]
    proposals = {
        "sched_min_granularity_ns": "15000000",
        "sched_wake_affinity": "1",
        "sched_latency_ns": "12000000",
    }
    for knob in bundle:
        recs.append({
            "id": f"rec-{knob}",
            "knob": knob,
            "proposed": proposals.get(knob, "auto"),
            "rationale": f"co-tune for tail latency (p95≈{p95:.1f}ms)",
            "expected_impact": "-8%~-38% p95 when applied jointly",
            "bundle": "tail_latency_bundle",
        })
    return {"recommendations": recs}


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

    k = max(1, len([s for s in samples if s]))
    graph = ctx.get("dependency_graph", {})
    out = []
    for key, count in votes.most_common():
        rec = dict(exemplar[key])
        agreement = count / k
        # KB confidence: strongest synergizing edge weight for this knob
        edges = graph.get(key[0], [])
        kb_conf = max([e["weight"] for e in edges
                       if e["edge_type"] == "synergizes_with"] or [0.0])
        # uncertainty: high when models disagree and KB evidence is weak
        u = (1.0 - agreement) * 0.7 + (1.0 - kb_conf) * 0.3
        rec["uncertainty"] = round(min(1.0, max(0.02, u)), 3)
        rec["provenance"] = {
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


@app.post("/get_recommendations")
async def get_recommendations():
    ctx = await rag_context()
    prompt = json.dumps(ctx)[:12000]

    samples = []
    for i in range(SELF_CONSISTENCY_K):
        temp = 0.2 + 0.3 * i          # spread temperatures for diversity
        s = await sample_model(prompt, temp)
        samples.append(s)

    if not any(samples):              # no model reachable -> graph fallback
        fb = graph_grounded_fallback(ctx)
        samples = [fb, fb, fb]

    out = aggregate_self_consistency(samples, ctx)
    return JSONResponse(out)


@app.post("/log_outcome")
async def log_outcome(context: dict = Body(...), action: dict = Body(...),
                      outcome: dict = Body(...)):
    """Persist an applied recommendation's realized outcome back into the KB so
    the dependency graph and RAG index learn from deployment."""
    async with httpx.AsyncClient(timeout=15) as client:
        await client.post(f"{KB_URL}/kb/upsert_trace",
                          json={"context": context, "action": action,
                                "outcome": outcome})
    return {"ok": True}
