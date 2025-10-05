from fastapi import FastAPI
from pydantic import BaseModel
import time, os

ROLLBACK_TAU = float(os.getenv("UQ_THRESHOLD", "0.55"))

app = FastAPI(title="safety-runtime")

class Recommendation(BaseModel):
    knob_name: str
    proposed_value: str
    rationale: str
    expected_impact: str
    uncertainty_score: float

@app.get("/health")
def health(): return {"ok": True, "tau": ROLLBACK_TAU}

@app.post("/apply")
def apply(rec: Recommendation):
    staged = ["canary", "ramp", "full"]
    # Decide based on uncertainty
    if rec.uncertainty_score >= ROLLBACK_TAU:
        return {"applied": False, "status": "rolled back (high-uncertainty)", "rolled_back": True, "stage": "canary"}
    # pretend staged rollout succeeded
    return {"applied": True, "status": f"applied {rec.knob_name}={rec.proposed_value} via staged rollout", "rolled_back": False, "stage": staged[-1]}
