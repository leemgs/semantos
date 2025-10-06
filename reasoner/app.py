import os, json, asyncio, httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse

KB_URL = os.environ.get("KB_URL", "http://kb-service:8000")
TELEMETRY_URL = os.environ.get("TELEMETRY_URL", "http://telemetry-agent:8000")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")

app = FastAPI(title="reasoner", version="0.2.0")

SYSTEM_PROMPT = """You are SemantOS Reasoner.
Generate guarded, explainable Linux kernel tuning recommendations based on the provided telemetry + KB retrieval.
Return a **single JSON object** with key "recommendations": a list of items.
Each item MUST include fields:
- id (string, unique)
- knob (string)
- proposed (string or number)
- rationale (short one-line reason)
- expected_impact (short, e.g., "-8% median, -12% P95")
- uncertainty (0..1)
- explanation (2-4 sentences explaining *why*, citing telemetry stats and KB cues; no markdown)
Avoid extra keys. Keep the JSON strictly parseable."""

async def fetch_json(client, method, url, **kwargs):
    r = await client.request(method, url, **kwargs)
    r.raise_for_status()
    return r.json()

async def rag_context():
    async with httpx.AsyncClient(timeout=10) as client:
        tele = await fetch_json(client, "GET", f"{TELEMETRY_URL}/snapshot")
        # vector retrieve based on workload/knob keywords
        q = f"workload:{tele['metrics'].get('cpu_load_1',0):.2f} p95:{tele['metrics'].get('p95_latency_ms',0):.2f}"
        nn = await fetch_json(client, "POST", f"{KB_URL}/kb/nn_search", json={"query": q, "k": 5})
        # graph sample (not filtering here for brevity)
        graph_ok = await fetch_json(client, "GET", f"{KB_URL}/healthz")
    return {"telemetry": tele, "nn": nn, "kb_health": graph_ok}

async def call_openai(prompt: str):
    import httpx, os, json
    key = os.environ["OPENAI_API_KEY"]
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": os.environ.get("OPENAI_MODEL","gpt-4o-mini"),
                  "response_format":{"type":"json_object"},
                  "messages":[{"role":"system","content":SYSTEM_PROMPT},
                              {"role":"user","content":prompt}]}
        )
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        try:
            return json.loads(content)
        except Exception:
            return {"recommendations":[]}


async def kb_dep_path(knob: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{KB_URL}/kb/dependency_path", params={"start": knob})
            r.raise_for_status()
            return r.json()
    except Exception:
        return {}

def enrich_with_dep_paths(obj):
    try:
        recs = obj.get("recommendations", [])
        for rec in recs:
            rec.setdefault("explanation", "")
        return obj
    except Exception:
        return obj


async def call_ollama(prompt: str):
    import httpx, json, os
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{OLLAMA_HOST}/api/generate",
            json={"model": os.environ.get("OLLAMA_MODEL","llama3.1"),
                  "prompt": SYSTEM_PROMPT + "\n" + prompt,
                  "format":"json"}
        )
        r.raise_for_status()
        # streaming format; get last JSON object
        lines = [ln for ln in r.text.splitlines() if ln.strip()]
        text = ""
        for ln in lines:
            try:
                obj = json.loads(ln)
                if "response" in obj:
                    text += obj["response"]
            except Exception:
                pass
        try:
            return json.loads(text)
        except Exception:
            return {"recommendations":[]}

def fallback_reasoner(ctx):
    # Heuristic: if p95 is high, propose lowering sched_min_granularity_ns and vm.dirty_ratio
    p95 = ctx["telemetry"]["metrics"].get("p95_latency_ms", 0)
    recs = []
    if p95 >= 20:
        recs.append({
            "id": "rec-auto-1",
            "knob": "sched_min_granularity_ns",
            "proposed": "15000000",
            "rationale": f"Reduce preemption quantum to tame tail latency (p95≈{p95}ms).",
            "expected_impact": "-5%~10% p95",
            "uncertainty": 0.42
        })
        recs.append({
            "id": "rec-auto-2",
            "knob": "vm.dirty_ratio",
            "proposed": "15",
            "rationale": "Reduce writeback bursts causing IO contention spikes.",
            "expected_impact": "-2%~6% p95; slight anomaly risk (guarded)",
            "uncertainty": 0.58
        })
    return {"recommendations": recs}

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/get_recommendations")
async def get_recommendations():
    ctx = await rag_context()
    prompt = json.dumps(ctx)
    if OPENAI_API_KEY:
        try:
            out = await call_openai(prompt)
            if "recommendations" in out and out["recommendations"]:
                return JSONResponse(out)
        except Exception:
            pass
    # Try Ollama if available
    try:
        out = await call_ollama(prompt)
        if "recommendations" in out and out["recommendations"]:
            return JSONResponse(out)
    except Exception:
        pass
    # Fallback heuristic
    out = fallback_reasoner(ctx)
    # add brief explanation using telemetry + (optional) dep neighbors
    for rec in out.get("recommendations", []):
        knob = rec.get("knob","")
        dep = asyncio.get_event_loop().run_until_complete(kb_dep_path(knob))
        nbrs = ", ".join(dep.get("neighbors", [])[:4]) if dep else ""
        p95 = ctx["telemetry"]["metrics"].get("p95_latency_ms", 0)
        rec["explanation"] = f"p95≈{p95}ms suggests tail sensitivity; KB neighbors: {nbrs}."
    return JSONResponse(out)
