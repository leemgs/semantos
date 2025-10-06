import os, time, glob, statistics, threading, asyncio, httpx
from typing import List, Dict
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse

# --- Config ---
TAU = float(os.environ.get("TAU","0.55"))
ROLL = [int(x) for x in os.environ.get("ROLLOUT_STEPS","5,25,50,100").split(",")]
SLO_MAX_P95 = float(os.environ.get("SLO_MAX_P95","35"))
LOG_DIR = os.environ.get("LOG_DIR","/app/outputs")
TELEMETRY_URL = os.environ.get("TELEMETRY_URL", "http://telemetry-agent:8000")
AUTO_POLL = os.environ.get("AUTO_POLL","on").lower()  # "on" | "off"
POLL_INTERVAL_SEC = int(os.environ.get("POLL_INTERVAL_SEC","10"))
ALERT_WEBHOOK = os.environ.get("ALERT_WEBHOOK","")  # generic webhook (Slack-compatible)

state = {
    "active": False,
    "rec_id": None,
    "percent": 0,
    "history": [],  # list of {ts, percent, p95, ok, source}
    "vetoed": []
}

app = FastAPI(title="safety-runtime", version="0.3.0")

def latest_p95_from_outputs() -> float:
    # Scan outputs logs for last values as proxy SLO
    logs = sorted(glob.glob(os.path.join(LOG_DIR, "*", "run_*.log")))
    if not logs:
        return 0.0
    p95s = []
    for path in logs[-6:]:  # sample a few recent logs
        try:
            with open(path, "r") as f:
                lines = f.read().strip().splitlines()[1:]
                if not lines:
                    continue
                *_, last = lines
                parts = last.split(",")
                # timestamp,metric,median_ms,p95_ms,throughput,anomaly_rate
                p95 = float(parts[3])
                p95s.append(p95)
        except Exception:
            pass
    return statistics.median(p95s) if p95s else 0.0

async def p95_from_telemetry() -> float:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{TELEMETRY_URL}/snapshot")
            r.raise_for_status()
            data = r.json()
            return float(data.get("metrics",{}).get("p95_latency_ms", 0.0))
    except Exception:
        return 0.0

def alert(text: str):
    if not ALERT_WEBHOOK:
        return
    try:
        import json, httpx
        with httpx.Client(timeout=5) as client:
            client.post(ALERT_WEBHOOK, json={"text": text})
    except Exception:
        pass

@app.get("/healthz")
def healthz():
    return {"ok": True, "tau": TAU, "rollout": ROLL, "slo_max_p95": SLO_MAX_P95, "auto_poll": AUTO_POLL, "poll_interval_sec": POLL_INTERVAL_SEC}

@app.post("/apply")
def apply(body: Dict = Body(...)):
    # body must include {"recommendations":[{id,knob,proposed,uncertainty,...}]}
    recs = body.get("recommendations", [])
    applied, vetoed = [], []
    for r in recs:
        if float(r.get("uncertainty", 1)) >= TAU:
            vetoed.append(r["id"])
        else:
            applied.append(r["id"])
    # Start rollout for first applied rec (demo)
    if applied and not state["active"]:
        state["active"] = True
        state["rec_id"] = applied[0]
        state["percent"] = ROLL[0]
        p95 = latest_p95_from_outputs()
        ok = p95 <= SLO_MAX_P95
        state["history"].append({"ts": time.time(), "percent": state["percent"], "p95": p95, "ok": ok, "source": "outputs"})
        alert(f"SemantOS: rollout started for {state['rec_id']} at {state['percent']}% (p95={p95}ms)")
    state["vetoed"].extend(vetoed)
    return JSONResponse({"applied": applied, "vetoed": vetoed, "tau": TAU})

@app.post("/rollout/advance")
def rollout_advance():
    if not state["active"]:
        return {"ok": False, "reason": "no_active_rollout"}
    idx = ROLL.index(state["percent"])
    if idx < len(ROLL) - 1:
        # Check SLO gate before advancing
        p95 = latest_p95_from_outputs()
        ok = p95 <= SLO_MAX_P95
        state["history"].append({"ts": time.time(), "percent": state["percent"], "p95": p95, "ok": ok, "source": "outputs"})
        if not ok:
            alert(f"SemantOS: rollout halted at {state['percent']}% due to SLO breach (p95={p95}ms > {SLO_MAX_P95})")
            state["active"] = False
            return {"ok": True, "stopped": True, "at": state["percent"], "p95": p95}
        state["percent"] = ROLL[idx+1]
        alert(f"SemantOS: rollout advanced to {state['percent']}% (p95={p95}ms)")
        return {"ok": True, "advanced_to": state["percent"]}
    else:
        state["active"] = False
        state["percent"] = 100
        alert(f"SemantOS: rollout completed for {state['rec_id']}")
        return {"ok": True, "completed": True}

@app.post("/rollback")
def rollback():
    if state["active"]:
        alert(f"SemantOS: manual rollback at {state['percent']}% for {state['rec_id']}")
    state["active"] = False
    state["percent"] = 0
    return {"ok": True, "rolled_back": True}

@app.get("/status")
def status():
    return state

# --- Background poller ---
def poller():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        try:
            time.sleep(POLL_INTERVAL_SEC)
            if not state["active"] or AUTO_POLL != "on":
                continue
            # Prefer realtime telemetry p95; fallback to outputs
            p95 = loop.run_until_complete(p95_from_telemetry()) or latest_p95_from_outputs()
            ok = p95 <= SLO_MAX_P95
            state["history"].append({"ts": time.time(), "percent": state["percent"], "p95": p95, "ok": ok, "source": "telemetry" if p95 else "outputs"})
            if not ok:
                # Auto rollback on breach
                alert(f"SemantOS: AUTO-ROLLBACK at {state['percent']}% for {state['rec_id']} (p95={p95}ms > {SLO_MAX_P95})")
                state["active"] = False
                state["percent"] = 0
        except Exception:
            # swallow exceptions to keep thread alive
            pass

@app.on_event("startup")
def startup():
    if AUTO_POLL == "on":
        t = threading.Thread(target=poller, daemon=True)
        t.start()
