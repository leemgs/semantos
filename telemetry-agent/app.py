from fastapi import FastAPI
from pydantic import BaseModel
import time, random, os
import httpx

KB_URL = os.getenv("KB_URL", "http://kb-service:7001")
REASONER_URL = os.getenv("REASONER_URL", "http://reasoner:7002")
SAFETY_URL = os.getenv("SAFETY_URL", "http://safety-runtime:7003")

app = FastAPI(title="telemetry-agent")

class TelemetrySnapshot(BaseModel):
    host: str
    workload: str
    timestamp_ms: int
    cpu_load: float
    mem_pressure: float
    rq_latency_ms: float

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/emit")
async def emit(snapshot: TelemetrySnapshot):
    # In a real system we would push to KB or Reasoner.
    async with httpx.AsyncClient(timeout=10.0) as client:
        # pretend to alert KB about new telemetry (mock no-op endpoint)
        try:
            await client.post(f"{KB_URL}/log_telemetry", json=snapshot.model_dump())
        except Exception:
            pass
        # ask reasoner for recs
        try:
            rec = await client.post(f"{REASONER_URL}/recommend", json=snapshot.model_dump())
            recj = rec.json()
            # ask safety-runtime to apply
            await client.post(f"{SAFETY_URL}/apply", json=recj)
        except Exception:
            pass
    return {"forwarded": True, "workload": snapshot.workload}

@app.post("/simulate_once")
async def simulate_once(workload: str = "web", host: str = "node-a"):
    snap = TelemetrySnapshot(
        host=host,
        workload=workload,
        timestamp_ms=int(time.time()*1000),
        cpu_load=random.uniform(0.2, 0.95),
        mem_pressure=random.uniform(0.1, 0.9),
        rq_latency_ms=random.uniform(1.0, 25.0),
    )
    return await emit(snap)
