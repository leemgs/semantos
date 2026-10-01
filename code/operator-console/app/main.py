from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import json, os, datetime, asyncio, httpx

app = FastAPI(title="SemantOS Operator Console", version="0.2.2")

BASE = Path(__file__).resolve().parents[1]
OUTPUTS = Path(os.environ.get("OUTPUTS_DIR", str(BASE / "outputs")))
DATA = Path(os.environ.get("CONSOLE_DATA_DIR", str(BASE / "app" / "data")))
DATA.mkdir(parents=True, exist_ok=True)

KB_URL = os.environ.get("KB_URL", "http://kb-service:8000")
SAFETY_URL = os.environ.get("SAFETY_URL", "http://safety-runtime:8000")
REASONER_URL = os.environ.get("REASONER_URL", "http://reasoner:8000")

# ❗ static 경로를 templates/static으로 마운트 (실존 폴더)
STATIC_DIR = DATA / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

class Recommendation(BaseModel):
    id: str
    knob: str
    proposed: str
    rationale: str
    expected_impact: str
    uncertainty: float
    status: str = "pending"
    explanation: str = ""

REC_FILE = DATA / "recommendations.json"
AUDIT_FILE = DATA / "audit_log.json"

def _load_json(p: Path, default):
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            return default
    return default

def _save_json(p: Path, obj):
    p.write_text(json.dumps(obj, indent=2))

def seed_if_needed():
    if not REC_FILE.exists():
        recs = []  # no fabricated recommendations
        _save_json(REC_FILE, recs)
    if not AUDIT_FILE.exists():
        _save_json(AUDIT_FILE, [])

seed_if_needed()

async def _get(client, url):
    r = await client.get(url, timeout=10)
    r.raise_for_status()
    return r.json()

async def _post(client, url, payload=None):
    r = await client.post(url, json=payload or {}, timeout=15)
    r.raise_for_status()
    return r.json()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # 서버 사이드에서는 로그 테이블만 렌더링, 추천 목록은 클라이언트에서 /api/recommendations로 로드
    workloads = ["web", "oltp", "streaming", "sensor", "hpc_ml", "audio"]
    rows = []
    for w in workloads:
        wdir = OUTPUTS / w
        latest = ""
        if wdir.exists():
            files = sorted([p.name for p in wdir.glob("run_*.log")])
            latest = files[-1] if files else ""
        rows.append(f"<tr><td>{w}</td><td>{latest or '<span class=muted>none</span>'}</td></tr>")

    html = """
<html>
<head>
  <title>SemantOS Operator Console</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body{font-family:system-ui,Segoe UI,Roboto,Arial,sans-serif;margin:20px;max-width:1100px}
    .card{border:1px solid #ddd;border-radius:12px;padding:16px;margin:12px 0;box-shadow:0 1px 2px rgba(0,0,0,0.04)}
    .row{display:flex;gap:12px;align-items:center;flex-wrap:wrap}
    .btn{padding:8px 14px;border-radius:10px;border:1px solid #ccc;cursor:pointer;background:#fff}
    .btn:hover{background:#f5f5f5}
    .pill{padding:2px 8px;border-radius:999px;border:1px solid #ccc}
    .ok{color:#0a0} .warn{color:#a60} .bad{color:#a00} .muted{color:#666}
    code{background:#f6f8fa;padding:2px 6px;border-radius:6px}
    table{border-collapse:collapse;width:100%} th,td{border:1px solid #eee;padding:8px;text-align:left}
    .title{display:flex;justify-content:space-between;align-items:center}
    .rec{border:1px solid #eee;border-radius:10px;padding:12px;margin:10px 0}
  </style>
</head>
<body>
  <div class="title">
    <h1>SemantOS Dry-run Console</h1>
    <div class="muted">v0.2.2</div>
  </div>

  <div class="card">
    <div class="row"><strong>Simulated rollout — no kernel settings are changed</strong>
      <button class="btn" onclick="refreshStatus()">Refresh</button>
      <button class="btn" onclick="advance()">Advance</button>
      <button class="btn" onclick="rollback()">Cancel simulation</button>
    </div>
    <div id="status" class="muted">Loading status...</div>
  </div>

  <div class="card">
    <strong>Telemetry Logs</strong>
    <table><thead><tr><th>Workload</th><th>Latest Log</th></tr></thead>
      <tbody>
        %LOGS%
      </tbody>
    </table>
  </div>

  <div class="card">
    <div class="row" style="justify-content:space-between;align-items:center;width:100%">
      <strong>Recommendations</strong>
      <div class="row">
        <button class="btn" onclick="refreshRecs()">Refresh from Reasoner</button>
      </div>
    </div>
    <div class="muted">Click “View Evidence” to see KB neighbors & dependency graph.</div>
    <div id="recs"></div>
  </div>

<script>
async function refreshStatus(){
  const r = await fetch('/api/status'); const d = await r.json();
  let line = `mode=${d.mode || "unavailable"} active=${d.active} percent=${d.percent}%`;
  if(d.rec_id) line += ` rec=${d.rec_id}`;
  if(d.vetoed && d.vetoed.length) line += ` vetoed=[${d.vetoed.join(', ')}]`;
  document.getElementById('status').innerHTML = line + '<br/>' + renderHistory(d.history || []);
}

function escapeHTML(value){
  const el = document.createElement('span'); el.textContent = String(value ?? ''); return el.innerHTML;
}
function renderHistory(h){
  return '<pre>'+escapeHTML(JSON.stringify(h || [], null, 2))+'</pre>';
}

async function advance(){ await fetch('/api/advance', {method:'POST'}); await refreshStatus(); }
async function rollback(){ await fetch('/api/rollback', {method:'POST'}); await refreshStatus(); }

function uBadge(u){
  const c = (u < 0.4 ? 'ok' : (u < 0.7 ? 'warn' : 'bad'));
  return `<span class="pill ${c}">u=${u.toFixed(2)}</span>`;
}

function recCard(r){
  return `
  <div class="rec">
    <div class="row" style="justify-content:space-between;align-items:flex-start">
      <div style="flex:1">
        <div><code>${r.knob}</code> → <code>${r.proposed}</code> ${uBadge(r.uncertainty)} <span class="pill">${r.status}</span></div>
        <div class="muted">${r.rationale} | expected: ${r.expected_impact}</div>
        ${r.explanation ? `<div style="margin-top:6px">${r.explanation}</div>` : ""}
      </div>
      <div class="row">
        <button class="btn" onclick="approve('${r.id}')">Simulate bundle</button>
        <button class="btn" onclick="rejectRec('${r.id}')">Reject</button>
        <button class="btn" onclick="rollbackRec('${r.id}')">Cancel simulation</button>
      </div>
    </div>
    <div style="margin-top:8px">
      <button class="btn" onclick="showEvidence('${r.id}')">View Evidence</button>
      <div id="ev-${r.id}" class="muted" style="margin-top:8px"></div>
    </div>
  </div>`;
}

async function loadRecs(){
  const r = await fetch('/api/recommendations'); const d = await r.json();
  const html = d.map(recCard).join('');
  document.getElementById('recs').innerHTML = html || '<span class="muted">no recommendations</span>';
}

async function refreshRecs(){
  await fetch('/api/refresh_recs',{method:'POST'});
  await loadRecs();
}

async function approve(id){
  const response = await fetch('/api/approve/'+encodeURIComponent(id), {method:'POST'});
  if (!response.ok) { alert(JSON.stringify(await response.json())); return; }
  await loadRecs();
  await refreshStatus();
}

async function rejectRec(id){
  await fetch('/api/reject/'+id, {method:'POST'});
  await loadRecs();
}

async function rollbackRec(id){
  await fetch('/api/rollback_rec/'+id, {method:'POST'});
  await loadRecs();
  await refreshStatus();
}

async function showEvidence(id){
  const r = await fetch('/api/rec_evidence/'+id);
  const d = await r.json();
  const el = document.getElementById('ev-'+id);
  if(d.error){ el.innerText = 'error: '+d.error; return; }
  let html = '';
  if(d.nn && d.nn.items && d.nn.items.length){
    html += '<div><strong>Vector Neighbors</strong><ol>'+d.nn.items.map(x=>`<li>${x.text} <span class="muted">(score ${x.score.toFixed(3)})</span></li>`).join('')+'</ol></div>';
  } else { html += '<div><strong>Vector Neighbors</strong> <span class="muted">none</span></div>'; }
  if(d.graph && d.graph.nodes && d.graph.nodes.length){
    html += '<div style="margin-top:6px"><strong>Dependency Path</strong> '+d.graph.nodes.join(' → ')+'</div>';
  } else if(d.graph && d.graph.neighbors){
    html += '<div style="margin-top:6px"><strong>Neighbors</strong> '+d.graph.neighbors.join(', ')+'</div>';
  } else { html += '<div style="margin-top:6px"><strong>Graph</strong> <span class="muted">none</span></div>'; }
  el.innerHTML = html;
}

window.addEventListener('load', async ()=>{ await loadRecs(); await refreshStatus(); });
</script>

</body></html>
""".replace("%LOGS%", "".join(rows))

    return HTMLResponse(html)

# ---------- API: recommendations & audit ----------
@app.get("/api/recommendations")
def api_recs():
    return JSONResponse(_load_json(REC_FILE, []))

@app.get("/api/audit")
def api_audit():
    return JSONResponse(_load_json(AUDIT_FILE, []))

def _append_audit(action, rec_id):
    logs = _load_json(AUDIT_FILE, [])
    logs.append({"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(), "action": action, "id": rec_id})
    _save_json(AUDIT_FILE, logs)

@app.post("/api/approve/{rec_id}")
async def approve(rec_id: str):
    recs = _load_json(REC_FILE, [])
    target = next((r for r in recs if r["id"] == rec_id), None)
    if target is None:
        raise HTTPException(404, "unknown recommendation")
    if not target.get("bundle"):
        raise HTTPException(422, "explicit bundle id required")
    bundle = [r for r in recs if r.get("bundle") == target["bundle"]]
    try:
        async with httpx.AsyncClient() as client:
            result = await _post(client, f"{SAFETY_URL}/apply", {"recommendations": bundle})
    except httpx.HTTPError as e:
        raise HTTPException(502, "runtime rejected or could not process the bundle") from e
    for rec in bundle:
        if rec["id"] in result.get("simulated", []): rec["status"] = "simulated"
        elif rec["id"] in result.get("vetoed", []): rec["status"] = "vetoed"
    _save_json(REC_FILE, recs)
    _append_audit("dry_run_bundle", target["bundle"])
    return result

@app.post("/api/reject/{rec_id}")
def reject(rec_id: str):
    recs = _load_json(REC_FILE, [])
    for r in recs:
        if r["id"] == rec_id:
            r["status"] = "rejected"
            _append_audit("reject", rec_id)
            break
    _save_json(REC_FILE, recs)
    return {"ok": True}

@app.post("/api/rollback_rec/{rec_id}")
async def rollback_rec(rec_id: str):
    recs = _load_json(REC_FILE, [])
    target = next((r for r in recs if r["id"] == rec_id), None)
    if target is None:
        raise HTTPException(404, "unknown recommendation")
    async with httpx.AsyncClient() as client:
        status = await _get(client, f"{SAFETY_URL}/status")
        if not target.get("bundle") or status.get("rec_id") != target["bundle"]:
            raise HTTPException(409, "this bundle is not staged")
        result = await _post(client, f"{SAFETY_URL}/rollback")
    for rec in recs:
        if rec.get("bundle") == target["bundle"]: rec["status"] = "simulation_cancelled"
    _save_json(REC_FILE, recs)
    _append_audit("cancel_simulated_bundle", target["bundle"])
    return result

# ---------- API: rollout / SLO ----------
@app.get("/api/status")
async def api_status():
    try:
        async with httpx.AsyncClient() as client:
            return JSONResponse(await _get(client, f"{SAFETY_URL}/status"))
    except Exception:
        return JSONResponse({"active": False, "percent": 0, "history": [], "vetoed": []})

@app.post("/api/advance")
async def api_advance():
    try:
        async with httpx.AsyncClient() as client:
            return JSONResponse(await _post(client, f"{SAFETY_URL}/rollout/advance"))
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})

@app.post("/api/rollback")
async def api_rollback():
    try:
        async with httpx.AsyncClient() as client:
            return JSONResponse(await _post(client, f"{SAFETY_URL}/rollback"))
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})

# ---------- API: refresh from reasoner ----------
@app.post("/api/refresh_recs")
async def refresh_recs():
    try:
        async with httpx.AsyncClient() as client:
            data = await _post(client, f"{REASONER_URL}/get_recommendations")
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})

    recs = data.get("recommendations", [])
    norm = []
    for r in recs:
        norm.append({
            "id": r.get("id",""),
            "bundle": r.get("bundle", ""),
            "provenance": r.get("provenance", {}),
            "knob": r.get("knob",""),
            "proposed": str(r.get("proposed","")),
            "rationale": r.get("rationale",""),
            "expected_impact": r.get("expected_impact",""),
            "uncertainty": float(r.get("uncertainty", 0.5)),
            "status": "pending",
            "explanation": r.get("explanation",""),
        })
    _save_json(REC_FILE, norm)
    return {"ok": True, "count": len(norm)}

# ---------- API: KB search & evidence ----------
@app.get("/api/kb_search")
async def api_kb_search(q: str):
    try:
        async with httpx.AsyncClient() as client:
            return JSONResponse(await _post(client, f"{KB_URL}/kb/nn_search", {"query": q, "k": 5}))
    except Exception as e:
        return JSONResponse({"items": [], "error": str(e)})

@app.get("/api/rec_evidence/{rec_id}")
async def rec_evidence(rec_id: str):
    recs = _load_json(REC_FILE, [])
    target = next((r for r in recs if r["id"] == rec_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="unknown recommendation id")
    knob = target["knob"]
    try:
        async with httpx.AsyncClient() as client:
            nn = await _post(client, f"{KB_URL}/kb/nn_search", {"query": knob, "k": 5})
            graph = await _get(client, f"{KB_URL}/kb/dependency_path?start={knob}")
    except Exception as e:
        return JSONResponse({"error": str(e)})
    return JSONResponse({"nn": nn, "graph": graph})
