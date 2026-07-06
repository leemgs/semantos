"""
safety-runtime — SemantOS conformal safety runtime (paper Sec. 4.4 / Alg. 1).

Responsibilities:
  * Gate each recommendation on a *conformally calibrated* veto threshold tau,
    derived from a sliding calibration log at miscoverage level alpha and refined
    by cost-based selection C(tau) (see safety_core.py).
  * Roll out survivors through canary -> ramp -> full stages, each guarded by an
    SLO check on live p95; auto-rollback on breach.
  * Detect drift (ADWIN over u) and recalibrate tau online.
  * Emit an OptimizationTrace (JSONL) capturing every gate/stage/rollback for
    auditability and for offline re-derivation of the paper's tau-sweep.
"""
import os
import time
import json
import glob
import statistics
import threading
import asyncio

import httpx
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse

from safety_core import SlidingCalibrator

# --------------------------------------------------------------------------- #
# Config.
# --------------------------------------------------------------------------- #
ALPHA = float(os.environ.get("CONFORMAL_ALPHA", "0.10"))
TAU_FLOOR = float(os.environ.get("TAU", "0.55"))
CAL_WINDOW = int(os.environ.get("CAL_WINDOW", "400"))
ROLL = [int(x) for x in os.environ.get("ROLLOUT_STEPS", "5,25,50,100").split(",")]
STAGE_NAMES = {0: "canary", 1: "ramp", 2: "ramp", 3: "full"}
SLO_MAX_P95 = float(os.environ.get("SLO_MAX_P95", "35"))
LOG_DIR = os.environ.get("LOG_DIR", "/app/outputs")
TRACE_PATH = os.environ.get("TRACE_PATH", "/app/outputs/optimization_trace.jsonl")
CAL_SEED_PATH = os.environ.get("CAL_SEED", "/app/data/calibration_seed.json")
TELEMETRY_URL = os.environ.get("TELEMETRY_URL", "http://telemetry-agent:8000")
AUTO_POLL = os.environ.get("AUTO_POLL", "on").lower()
POLL_INTERVAL_SEC = int(os.environ.get("POLL_INTERVAL_SEC", "10"))
ALERT_WEBHOOK = os.environ.get("ALERT_WEBHOOK", "")

COST = {"c_fn": float(os.environ.get("C_FN", "4.0")),
        "c_fp": float(os.environ.get("C_FP", "6.0")),
        "lam": float(os.environ.get("LAMBDA", "0.5")),
        "slo_budget_delta": float(os.environ.get("SLO_BUDGET_DELTA", "0.5"))}

calibrator = SlidingCalibrator(alpha=ALPHA, window=CAL_WINDOW,
                               tau_floor=TAU_FLOOR, cost=COST)

state = {
    "active": False, "rec_id": None, "percent": 0, "stage": None,
    "history": [], "vetoed": [], "tau": calibrator.tau,
}

app = FastAPI(title="safety-runtime", version="1.0.0")


def _seed_calibration():
    """Warm-start D_cal from a bundled calibration log if present."""
    try:
        if os.path.exists(CAL_SEED_PATH):
            recs = json.loads(open(CAL_SEED_PATH).read())
            for r in recs:
                calibrator.observe(float(r["u"]), bool(r["unsafe"]))
            calibrator.recalibrate()
            state["tau"] = calibrator.tau
    except Exception:
        pass


def _trace(event: str, payload: dict):
    rec = {"ts": time.time(), "event": event, **payload}
    try:
        os.makedirs(os.path.dirname(TRACE_PATH), exist_ok=True)
        with open(TRACE_PATH, "a") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception:
        pass
    return rec


def alert(text: str):
    if not ALERT_WEBHOOK:
        return
    try:
        with httpx.Client(timeout=5) as client:
            client.post(ALERT_WEBHOOK, json={"text": text})
    except Exception:
        pass


def latest_p95_from_outputs() -> float:
    logs = sorted(glob.glob(os.path.join(LOG_DIR, "*", "run_*.log")))
    p95s = []
    for path in logs[-6:]:
        try:
            lines = open(path).read().strip().splitlines()[1:]
            if lines:
                p95s.append(float(lines[-1].split(",")[3]))
        except Exception:
            pass
    return statistics.median(p95s) if p95s else 0.0


async def p95_from_telemetry() -> float:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{TELEMETRY_URL}/snapshot")
            r.raise_for_status()
            return float(r.json().get("metrics", {}).get("p95_latency_ms", 0.0))
    except Exception:
        return 0.0


@app.get("/healthz")
def healthz():
    return {"ok": True, "tau": calibrator.tau, "alpha": ALPHA,
            "rollout": ROLL, "slo_max_p95": SLO_MAX_P95,
            "recalibrations": calibrator.recalibrations,
            "cal_records": calibrator.metrics()["n"]}


@app.post("/calibrate")
def calibrate(records: list = Body(default=None)):
    """Feed calibration records [{u, unsafe}] and recompute tau."""
    if records:
        for r in records:
            calibrator.observe(float(r["u"]), bool(r["unsafe"]))
    tau = calibrator.recalibrate()
    state["tau"] = tau
    m = calibrator.metrics()
    _trace("calibrate", {"tau": tau, "precision": m["precision"],
                         "recall": m["recall"], "n": m["n"]})
    return {"tau": tau, **m}


@app.post("/apply")
def apply(body: dict = Body(...)):
    """Gate recommendations on the calibrated tau; start staged rollout."""
    recs = body.get("recommendations", [])
    tau = calibrator.tau
    applied, vetoed = [], []
    for r in recs:
        u = float(r.get("uncertainty", 1.0))
        decision = "veto" if u >= tau else "apply"
        _trace("gate", {"rec_id": r.get("id"), "knob": r.get("knob"),
                        "u": u, "tau": tau, "decision": decision,
                        "bundle": r.get("bundle")})
        (vetoed if decision == "veto" else applied).append(r.get("id"))

    if applied and not state["active"]:
        state.update(active=True, rec_id=applied[0], percent=ROLL[0],
                     stage=STAGE_NAMES.get(0, "canary"))
        p95 = latest_p95_from_outputs()
        ok = p95 <= SLO_MAX_P95 or p95 == 0.0
        state["history"].append({"ts": time.time(), "percent": state["percent"],
                                 "stage": state["stage"], "p95": p95, "ok": ok})
        _trace("rollout_start", {"rec_id": state["rec_id"],
                                 "stage": state["stage"], "percent": state["percent"],
                                 "p95": p95})
        alert(f"SemantOS: canary started for {state['rec_id']} "
              f"({state['percent']}%, p95={p95}ms, tau={tau:.3f})")
    state["vetoed"].extend(vetoed)
    return JSONResponse({"applied": applied, "vetoed": vetoed, "tau": tau})


@app.post("/rollout/advance")
def rollout_advance():
    if not state["active"]:
        return {"ok": False, "reason": "no_active_rollout"}
    idx = ROLL.index(state["percent"])
    p95 = latest_p95_from_outputs()
    ok = p95 <= SLO_MAX_P95 or p95 == 0.0
    state["history"].append({"ts": time.time(), "percent": state["percent"],
                             "stage": state["stage"], "p95": p95, "ok": ok})
    if not ok:
        _trace("rollback", {"rec_id": state["rec_id"], "reason": "slo_breach",
                            "percent": state["percent"], "p95": p95})
        alert(f"SemantOS: rollout halted at {state['percent']}% "
              f"(p95={p95} > {SLO_MAX_P95})")
        state.update(active=False, percent=0, stage=None)
        return {"ok": True, "stopped": True, "p95": p95}
    if idx < len(ROLL) - 1:
        state["percent"] = ROLL[idx + 1]
        state["stage"] = STAGE_NAMES.get(idx + 1, "ramp")
        _trace("rollout_advance", {"rec_id": state["rec_id"],
                                   "stage": state["stage"],
                                   "percent": state["percent"], "p95": p95})
        alert(f"SemantOS: advanced to {state['stage']} {state['percent']}%")
        return {"ok": True, "advanced_to": state["percent"], "stage": state["stage"]}
    _trace("rollout_complete", {"rec_id": state["rec_id"], "p95": p95})
    state.update(active=False, percent=100, stage="full")
    alert(f"SemantOS: rollout completed for {state['rec_id']}")
    return {"ok": True, "completed": True}


@app.post("/rollback")
def rollback():
    if state["active"]:
        _trace("rollback", {"rec_id": state["rec_id"], "reason": "manual",
                            "percent": state["percent"]})
        alert(f"SemantOS: manual rollback at {state['percent']}%")
    state.update(active=False, percent=0, stage=None)
    return {"ok": True, "rolled_back": True}


@app.post("/log_outcome")
def log_outcome(rec_id: str = Body(...), u: float = Body(...),
                unsafe: bool = Body(...)):
    """Record a realized (u, unsafe) outcome into D_cal; drift -> recalibrate."""
    drift = calibrator.observe(float(u), bool(unsafe))
    state["tau"] = calibrator.tau
    m = calibrator.metrics()
    _trace("outcome", {"rec_id": rec_id, "u": u, "unsafe": unsafe,
                       "drift": drift, "tau": calibrator.tau,
                       "precision": m["precision"]})
    return {"ok": True, "drift": drift, "tau": calibrator.tau,
            "recalibrations": calibrator.recalibrations}


@app.get("/status")
def status():
    return {**state, "calibration": calibrator.metrics(),
            "recalibrations": calibrator.recalibrations}


# --------------------------------------------------------------------------- #
# Background SLO poller with auto-rollback.
# --------------------------------------------------------------------------- #
def poller():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        try:
            time.sleep(POLL_INTERVAL_SEC)
            if not state["active"] or AUTO_POLL != "on":
                continue
            p95 = loop.run_until_complete(p95_from_telemetry()) or \
                latest_p95_from_outputs()
            ok = p95 <= SLO_MAX_P95 or p95 == 0.0
            state["history"].append({"ts": time.time(), "percent": state["percent"],
                                     "stage": state["stage"], "p95": p95, "ok": ok})
            if not ok:
                _trace("rollback", {"rec_id": state["rec_id"],
                                    "reason": "auto_slo_breach",
                                    "percent": state["percent"], "p95": p95})
                alert(f"SemantOS: AUTO-ROLLBACK at {state['percent']}% "
                      f"(p95={p95} > {SLO_MAX_P95})")
                state.update(active=False, percent=0, stage=None)
        except Exception:
            pass


@app.on_event("startup")
def startup():
    _seed_calibration()
    if AUTO_POLL == "on":
        threading.Thread(target=poller, daemon=True).start()
