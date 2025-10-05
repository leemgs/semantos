from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
import time

app = FastAPI(title="kb-service")

class Telemetry(BaseModel):
    host: str
    workload: str
    timestamp_ms: int
    cpu_load: float
    mem_pressure: float
    rq_latency_ms: float

KB_EDGES = [
    {"from":"sched_min_granularity_ns","to":"sched_wake_affinity","rel":"co-optimizes-with"},
    {"from":"vm.swappiness","to":"dirty_ratio","rel":"affects"},
]

@app.get("/health")
def health(): return {"ok": True}

@app.post("/retrieve_context")
def retrieve_context(tel: Telemetry):
    # Simple rules to return relevant "context"
    relevant = []
    if tel.workload in ("web","streaming","audio"):
        relevant.append({"hint":"reduce sched_latency_ns to lower tail latency"})
    if tel.mem_pressure > 0.7:
        relevant.append({"hint":"consider lowering vm.swappiness when memory pressure is high"})
    return {"edges": KB_EDGES, "hints": relevant}

@app.post("/log_telemetry")
def log_telemetry(tel: Telemetry):
    # In-memory no-op
    return {"logged": True, "ts": tel.timestamp_ms}
