# SemantOS: Semantic-Aware Kernel Optimization via Safe and Automated Sysctl Orchestration [Reproducibile Kit]

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](./LICENSE.md)  
[![Python](https://img.shields.io/badge/python-3.10%2B-brightgreen.svg)](#quickstart)  
[![Status](https://img.shields.io/badge/status-reproducible-lightgrey.svg)](#reproducing-paper-results)

---

## 🧠 Overview

**SemantOS** is an executable reference framework that transforms low-level Linux kernel parameter tuning from a manual, heuristic-driven task into a **semantic, safe, and automated orchestration pipeline**.  
Originally designed to reproduce the results of our research paper, this toolkit can be extended for real-world production environments — bridging the gap between academic reproducibility and operational deployment.

---

## 📦 Quickstart

```bash
# 0) Python 3.10+ recommended
python -V

# 1) (Optional) Create a virtual environment
python -m venv .venv && source .venv/bin/activate

# 2) Install (no external dependencies required)
pip install -e .

# 3) Run the full pipeline (sandbox mode)
bash experiments/run_reproduction.sh
```

Expected outputs:
- `experiments/sandbox/sysctl.conf` — applied configurations (sandboxed)
- `experiments/results/summary.csv` — baseline vs tuned p95 and improvement (%)

---

## 📁 Repository Structure

```
semantos/
  telemetry/       # synthetic telemetry generation
  kb/              # minimal knowledge base (JSON + catalog)
  reasoning/       # deterministic reasoning engine (LLM placeholder)
  safety/          # guardrails + sandbox sysctl logic
  rollout/         # batch rollout + applier + monitor
  eval/            # evaluator + CSV export tools
experiments/
  configs/         # example YAML configs
  data/            # sample telemetry CSV
  results/         # generated results
  sandbox/         # sandbox sysctl file lives here
tests/             # minimal unit tests
```

---

## 🧪 Reproducing Paper Results

This repository allows you to reproduce the results and figures from the paper with minimal setup.

- **Latency Improvement:**  
  `experiments/results/summary.csv` shows baseline and tuned median p95 latency across multiple trials.

- **Run with custom seeds:**  
```bash
python -m semantos.cli --seed 7 --trials 20
```

---

## 🧩 Extending with Real Systems

SemantOS is designed for real-world applicability. You can extend it beyond synthetic benchmarks by replacing key components:

1. **Telemetry:** Replace `telemetry/simulators.py` with actual eBPF or perf-based telemetry collectors.  
2. **Reasoning Engine:** Swap `reasoning/engine.py` with an LLM inference backend — guardrails in `safety/guardrails.py` will still ensure safe recommendations.  
3. **Applier:** Implement a privileged applier for remote or distributed hosts (not included in the base release).

---

## 🔒 Real `/proc/sys` Mode (Production)

> ⚠️ **Warning:** Changing kernel parameters on a live system can impact stability.  
> SemantOS provides **whitelisting**, **guardrails**, and **backup/rollback** support. Always deploy changes incrementally.

### Dry Run (Recommended)

```bash
bash experiments/run_sysctl_dryrun.sh
# or
python -m semantos.cli --applier sysctl
```

### Apply Changes (Requires root)

```bash
sudo -E bash experiments/run_sysctl_apply.sh
# or
sudo -E python -m semantos.cli --applier sysctl --apply
```

During application:
- Original values are saved to `experiments/backup/sysctl_backup.json`
- Whitelist includes:  
  - `vm.dirty_*`, `vm.swappiness`  
  - `net.core.{somaxconn, netdev_max_backlog}`  
  - `kernel.{sched_latency_ns, sched_min_granularity_ns, numa_balancing}`
- Operations abort on any guardrail violation.

### Rollback (Requires root)

```bash
sudo -E bash experiments/run_sysctl_rollback.sh
# or
sudo -E python -m semantos.cli --applier sysctl --rollback
```

---

## 📊 Output Artifacts

| Artifact | Description |
|----------|------------|
| `sysctl.conf` | Recommended kernel parameter settings (sandboxed) |
| `summary.csv` | p95 latency comparison before/after tuning |
| `sysctl_backup.json` | Auto-generated backup of original kernel parameters |
| `logs/` | Optional logs for rollout and validation |

---

## 🪄 Roadmap

- [ ] Plug-and-play integration with large language models (LLMs)  
- [ ] Support for remote kernel configuration via SSH and Ansible  
- [ ] Reinforcement learning–based policy optimization  
- [ ] Extended telemetry collectors (eBPF, perf, cgroup metrics)  

---

## 📜 License

This project is licensed under the **Apache 2.0 License**. See [LICENSE.md](./LICENSE.md) for details.


