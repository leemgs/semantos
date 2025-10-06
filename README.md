# SemantOS

A lightweight, containerized **semantic OS tuning** playground that closes the loop between **eBPF-style telemetry**, a **graph-backed knowledge base (Neo4j + FAISS)**, a **Reasoner** that can talk to external LLMs, and a **Safety Runtime** that enforces staged rollouts/automatic rollback. An **Operator Console** (FastAPI) glues the services together.

> This repository is intended for local experimentation, demos, and reproducible benchmarks—not for production hardening.

---

## ✨ What’s inside

```
semantos/
├─ docker-compose.yml                 # one-command bring-up of all services
├─ docker-compose.ebpf.yml            # extra privileges/mounts for eBPF sampling
├─ manual.sh                          # build, up, and tail logs helper
├─ proto/semantos-control.v1.yaml     # REST/OpenAPI for the control plane
├─ kb-service/                        # Neo4j + FAISS-backed knowledge base APIs
├─ reasoner/                          # LLM-backed (or heuristic) recommendation service
├─ safety-runtime/                    # staged rollout & auto-rollback gatekeeper
├─ telemetry-agent/                   # psutil + (optional) eBPF-derived metrics
├─ operator-console/                  # simple FastAPI UI (port 9988)
└─ workloads/                         # log-generating workload simulators
```

**Core services & default ports**

| Service           | Port (host:container) | Purpose |
|-------------------|------------------------|---------|
| Neo4j             | 7474, 7687             | Graph KB backing store |
| `kb-service`      | 9101:8000 *(via compose)* | Tunable graph, FAISS retrieval, path/neighbor queries |
| `telemetry-agent` | 9100:8000 *(example)* | Sliding-window metrics (median, p95, syscall rate) |
| `reasoner`        | 9102:8000 *(example)* | Generates explainable tuning candidates |
| `safety-runtime`  | 9103:8000 *(example)* | Canary→Ramp→Full rollouts, SLO guard, rollback |
| `operator-console`| **9988:9988**         | Minimal web UI / API aggregator |

> Tip: If **9988** is taken, change the host port in `docker-compose.yml` (e.g., `8088:9988`). See _Troubleshooting_.

---

## 🧱 Prerequisites

- Docker Engine 24+ and Docker Compose v2
- ~6–8 GB free RAM for Neo4j + Python services
- (Optional) Linux host with kernel headers if you want eBPF sampling
```bash
sudo apt-get update
sudo apt-get install -y linux-headers-$(uname -r)
```

---

## 🚀 Quick start

### 1) Bring up the stack

```bash
# From repo root
docker compose -f docker-compose.yml build
docker compose -f docker-compose.yml up -d

# Or use the convenience script
./manual.sh
```

Once healthy:
- Console: http://localhost:9988
- Neo4j Browser: http://localhost:7474 (user: `neo4j`, pass: `password` by default)

### 2) (Optional) Enable eBPF sampling

If your host supports eBPF and has headers installed, add the privileged bits with the overlay file:

```bash
docker compose -f docker-compose.yml -f docker-compose.ebpf.yml up -d
```

The `telemetry-agent` will attempt to auto-detect eBPF (`USE_EBPF=auto`). You can force it with `USE_EBPF=on`.

---

## 🔌 Services overview

### telemetry-agent
- FastAPI service exposing sliding-window metrics like `median_latency_ms`, `p95_latency_ms`, `sys_enter_rps`, etc.
- Uses `psutil` and—if enabled—basic eBPF probes (via BCC) to enrich signals.
- Env vars: `USE_EBPF=auto|on|off`, `SAMPLE_WINDOW=60`

### kb-service
- Talks to **Neo4j** (graph of tunables and dependencies) and **FAISS** (vector search).
- Provides simple REST endpoints for shortest paths, neighborhood queries, and retrieval support for the reasoner.
- Env vars: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASS`, `DATA_DIR=/data`

### reasoner
- Aggregates telemetry + KB context; calls an external LLM (OpenAI/Ollama) when available, otherwise falls back to heuristics.
- Env vars: `KB_URL`, `TELEMETRY_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `OLLAMA_HOST`, `OLLAMA_MODEL`

### safety-runtime
- Staged rollout controller with SLO guardrails and auto-rollback.
- Env vars: `TAU=0.55`, `ROLLOUT_STEPS=5,25,50,100`, `SLO_MAX_P95=35`, `AUTO_POLL=on|off`, `POLL_INTERVAL_SEC=10`

### operator-console
- Small FastAPI app that proxies to the services and serves a minimal UI.
- Exposes port **9988** on the host by default and writes artifacts to `./outputs/` (mounted into the container).

---

## 🧪 Reproducible workloads

Synthetic workload simulators live in `workloads/`. They log CSV-like lines into `./outputs/<workload>/…` with fields such as median, p95, throughput, and anomaly-rate (basis points).

Run them all:

```bash
./workloads/run_workload.sh
```

Or pick a subset:

```bash
./workloads/run_workload.sh web audio
```

---

## 🧭 Control-plane API

OpenAPI spec: `proto/semantos-control.v1.yaml`

- `POST /get_recommendations` — reasoner returns candidate knob updates with rationales
- `POST /apply` — safety runtime applies a candidate via staged rollout
- `POST /log_outcome` — persist outcomes for learning/auditability

These are intentionally minimal for hackability.

---

## ⚙️ Configuration & environment

Common knobs you may want to tweak in `docker-compose.yml`:

- **Ports**: Change the host-side port mapping if something is occupied (e.g., `8088:9988` for operator-console).
- **Neo4j storage**: Named volumes `neo4j_data`, `neo4j_logs` are declared at the bottom of the compose file.
- **eBPF**: Overlay with `docker-compose.ebpf.yml`, and ensure `/lib/modules`, `/usr/src`, and debugfs mounts exist.

---

## 🧰 Troubleshooting

### Port **9988** already allocated
If you see:
```
Bind for 0.0.0.0:9988 failed: port is already allocated
```
Edit `docker-compose.yml` and change the host port mapping for the `operator-console` service, e.g.:
```yaml
  operator-console:
    ports:
      - "8088:9988"   # was 9988:9988
```
Then rerun:
```bash
docker compose up -d --force-recreate
```

### Neo4j connection/auth errors
- Confirm the container is healthy and the env matches `NEO4J_*` in `kb-service`.
- Reset the password via `NEO4J_AUTH=neo4j/<new-pass>` (compose env).

### eBPF permission issues
- Use the `docker-compose.ebpf.yml` overlay (adds `privileged: true`, `pid: "host"`, and relevant mounts).
- Ensure kernel headers and `bcc` tools are available on the host.

### Nothing shows in the console
- Check individual service logs:
  ```bash
  docker compose logs telemetry-agent
  docker compose logs kb-service
  docker compose logs reasoner
  docker compose logs safety-runtime
  docker compose logs operator-console
  ```

---

## 📂 Outputs

All generated artifacts/logs are written under `./outputs/` on the host and mounted into corresponding containers (e.g., safety-runtime, operator-console).

---

## 🔐 Security notes

This is a local demo environment:
- Default credentials, open ports, and permissive CORS may be present.
- **Do not** expose to the public internet without hardening (auth, TLS, network policies, resource limits, etc.).

---

## 📝 License

Apache 2.0
