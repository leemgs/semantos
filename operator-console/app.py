from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import httpx
import os
import pathlib

# 보수적 방어: static 디렉토리가 없으면 생성
static_dir = pathlib.Path("static")
static_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="operator-console")
app.mount("/static", StaticFiles(directory="static"), name="static")

# 백엔드 서비스 주소 (Docker Compose 서비스명 기반 DNS)
TELEMETRY_URL = os.getenv("TELEMETRY_URL", "http://telemetry-agent:7000")
KB_URL        = os.getenv("KB_URL",        "http://kb-service:7001")
REASONER_URL  = os.getenv("REASONER_URL",  "http://reasoner:7002")
SAFETY_URL    = os.getenv("SAFETY_URL",    "http://safety-runtime:7003")

INDEX = """\
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>SemantOS Operator Console</title>
    <style>
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; padding: 24px; background: #fff; }
      .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
      .card { border: 1px solid #e5e7eb; border-radius: 16px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,.04); }
      .row { display:flex; gap:12px; align-items:center; }
      button { padding: 8px 12px; border-radius: 10px; border: 1px solid #e5e7eb; background: #f9fafb; cursor: pointer; }
      h1 { margin-top:0; font-size: 22px; }
      .muted { color:#6b7280; font-size:12px; }
      code { background:#f3f4f6; padding:2px 6px; border-radius:6px; }
      .log { white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; background:#0a0a0a; color:#e5e7eb; padding:12px; border-radius:12px; height: 180px; overflow:auto;}
      label { font-size: 12px; color:#374151; }
      input, select { padding:8px; border-radius:8px; border:1px solid #e5e7eb; width: 100%; }
    </style>
  </head>
  <body>
    <h1>SemantOS Operator Console</h1>
    <p class="muted">Review recommendations, apply via safety runtime, and simulate workloads. Backend services are mocked for reproducibility.</p>

    <div class="grid">
      <div class="card">
        <h3>1) Health</h3>
        <div class="row">
          <button onclick="checkHealth()">Check services</button>
        </div>
        <div id="health" class="log"></div>
      </div>

      <div class="card">
        <h3>2) Simulate Telemetry</h3>
        <label>Workload</label>
        <select id="workload">
          <option value="web">web</option>
          <option value="oltp">oltp</option>
          <option value="streaming">streaming</option>
          <option value="sensor">sensor</option>
          <option value="hpc_ml">hpc_ml</option>
          <option value="audio">audio</option>
        </select>
        <div class="row" style="margin-top:8px;">
          <button onclick="simulate()">Emit snapshot → rec → safety</button>
        </div>
        <div id="simlog" class="log"></div>
      </div>

      <div class="card">
        <h3>3) Manual Recommend/Apply</h3>
        <label>RQ latency (ms)</label>
        <input id="rq" type="number" value="12" />
        <div class="row" style="margin-top:8px;">
          <button onclick="manualRec()">Get recommendation</button>
          <button onclick="apply()">Apply via safety</button>
        </div>
        <div id="rec" class="log"></div>
      </div>
    </div>

    <!-- 인라인 스크립트 제거: 외부 파일로 교체 -->
    <script src="/static/app.js"></script>
  </body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(INDEX)

async def proxy_json(method: str, url: str, payload=None):
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.request(method, url, json=payload)
        # 단순 프록시: 응답 본문 JSON을 그대로 반환
        return r.json()

# --- Telemetry proxies ---
@app.get("/api/telemetry/health")
async def t_h():
    return await proxy_json("GET", f"{TELEMETRY_URL}/health")

@app.post("/api/telemetry/simulate_once")
async def t_s(workload: str = "web"):
    # 주의: telemetry-agent는 쿼리스트링 기반 파라미터를 기대하므로 그대로 전달
    url = f"{TELEMETRY_URL}/simulate_once?workload={workload}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(url)
        return r.json()

# --- KB proxies ---
@app.get("/api/kb/health")
async def k_h():
    return await proxy_json("GET", f"{KB_URL}/health")

# --- Reasoner proxies ---
@app.get("/api/reasoner/health")
async def r_h():
    return await proxy_json("GET", f"{REASONER_URL}/health")

@app.post("/api/reasoner/recommend")
async def r_r(req: Request):
    data = await req.json()
    return await proxy_json("POST", f"{REASONER_URL}/recommend", data)

# --- Safety proxies ---
@app.get("/api/safety/health")
async def s_h():
    return await proxy_json("GET", f"{SAFETY_URL}/health")

@app.post("/api/safety/apply")
async def s_a(req: Request):
    data = await req.json()
    return await proxy_json("POST", f"{SAFETY_URL}/apply", data)

