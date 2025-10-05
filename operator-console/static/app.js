// operator-console/static/app.js

function safeText(el, text){ try { el.textContent = text; } catch(e){} }
function ts(){ return new Date().toISOString(); }

async function j(url, opts){
  try{
    const r = await fetch(url, opts || {});
    const text = await r.text();
    try {
      return { ok: true, status: r.status, json: JSON.parse(text) };
    } catch {
      return { ok: r.ok, status: r.status, text };
    }
  } catch(e){
    return { ok: false, error: String(e) };
  }
}

async function checkHealth(){
  const box = document.getElementById("health");
  safeText(box, `[${ts()}] Checking services...`);
  const result = [];
  result.push(["telemetry", await j("/api/telemetry/health")]);
  result.push(["kb",        await j("/api/kb/health")]);
  result.push(["reasoner",  await j("/api/reasoner/health")]);
  result.push(["safety",    await j("/api/safety/health")]); // ← 여분의 ']' 금지
  safeText(box, JSON.stringify(result, null, 2));
}

async function simulate(){
  const box = document.getElementById("simlog");
  const w = document.getElementById("workload").value;
  safeText(box, `[${ts()}] Simulating workload: ${w} ...`);
  const r = await j(
    "/api/telemetry/simulate_once?workload=" + encodeURIComponent(w),
    { method: "POST" }
  );
  safeText(box, JSON.stringify(r, null, 2));
}

let lastRec = null;
async function manualRec(){
  const box = document.getElementById("rec");
  const rq = parseFloat(document.getElementById("rq").value || "12");
  const payload = {
    host: "node-a",
    workload: "web",
    timestamp_ms: Date.now(),
    cpu_load: 0.7,
    mem_pressure: 0.6,
    rq_latency_ms: rq
  };
  safeText(box, `[${ts()}] Getting recommendation...`);
  const r = await j("/api/reasoner/recommend", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(payload)
  });
  lastRec = r.json || r.text || r;
  safeText(box, JSON.stringify(lastRec, null, 2));
}

async function apply(){
  const box = document.getElementById("rec");
  if(!lastRec){
    safeText(box, "No recommendation yet. Click 'Get recommendation' first.");
    return;
  }
  const r = await j("/api/safety/apply", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(lastRec)
  });
  const prev = box.textContent || "";
  safeText(box, prev + "\n\nAPPLY RESULT:\n" + JSON.stringify(r, null, 2));
}

// Ensure functions are available for inline onclick handlers
window.checkHealth = checkHealth;
window.simulate = simulate;
window.manualRec  = manualRec;
window.apply      = apply;
