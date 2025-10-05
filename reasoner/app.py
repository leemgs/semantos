from fastapi import FastAPI
from pydantic import BaseModel
import os, httpx, random

KB_URL = os.getenv("KB_URL", "http://kb-service:7001")

app = FastAPI(title="reasoner")

class Telemetry(BaseModel):
    host: str
    workload: str
    timestamp_ms: int
    cpu_load: float
    mem_pressure: float
    rq_latency_ms: float

@app.get("/health")
def health(): return {"ok": True}

@app.post("/recommend")
async def recommend(tel: Telemetry):
    # retrieve context
    hints = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            ctx = await client.post(f"{KB_URL}/retrieve_context", json=tel.model_dump())
            hints = ctx.json().get("hints", [])
        except Exception:
            pass

    # toy policy producing a recommendation + uncertainty
    knob = "sched_min_granularity_ns"
    proposed = "2000000" if tel.rq_latency_ms > 10 else "1500000"
    rationale = "Reduced granularity to lower tail latency under observed RQ latency; co-optimizes with wake_affinity"
    if hints:
        rationale += f" | evidence: {hints[0]['hint']}"

    # uncertainty: higher when cpu/mem pressures are both high
    u = min(1.0, max(0.0, 0.3 + 0.4*(tel.cpu_load>0.8) + 0.3*(tel.mem_pressure>0.8)))
    return {
        "knob_name": knob,
        "proposed_value": proposed,
        "rationale": rationale,
        "expected_impact": "latency↓; anomaly rate↔/↓",
        "uncertainty_score": u
    }
