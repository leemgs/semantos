# SemantOS — Reproduction Kit

This repository provides an **executable reference pipeline** that mirrors the paper’s stages:

1. **Telemetry** (synthetic) →
2. **Knowledge Base** (lightweight JSON store) →
3. **Reasoning Engine** (deterministic rule-based stub standing in for the LLM) →
4. **Safety Guardrails** (bounds & relational checks) →
5. **Staggered Rollout** (sandboxed sysctl file; no privileged ops) →
6. **Monitoring** (synthetic post-check) →
7. **Evaluation** (median p95 comparison across trials)

> ⚠️ **Safety**: This kit never writes to `/proc` or `/sys`. All configuration changes are logged to `experiments/sandbox/sysctl.conf`.

---

## Quickstart

```bash
# 0) Python 3.10+ recommended
python -V

# 1) (Optional) create venv
python -m venv .venv && source .venv/bin/activate

# 2) Install (nothing external required)
pip install -e .

# 3) Run the full pipeline
bash experiments/run_reproduction.sh
```

Expected output includes:
- `experiments/sandbox/sysctl.conf` — applied configs (sandbox only)
- `experiments/results/summary.csv` — baseline vs tuned p95 and improvement percent

---

## Structure

```
semantos/
  telemetry/       # synthetic telemetry
  kb/              # minimal KB (JSON + catalog)
  reasoning/       # rule-based engine (LLM stand-in)
  safety/          # guardrails + sandbox sysctl
  rollout/         # batching + applier + monitor
  eval/            # evaluator and CSV export
experiments/
  configs/         # example configs (YAML for humans)
  data/            # sample telemetry CSV
  results/         # produced by runs
  sandbox/         # sysctl sandbox file lives here
tests/             # tiny unit tests
```

---

## Reproducing Paper Figures/Tables (Minimal)

- **Latency Improvement**: `experiments/results/summary.csv` contains baseline and tuned median p95 across N trials.
- You can repeat with different seeds:  
  `python -m semantos.cli --seed 7 --trials 20`

---

## Extending with Real Systems

1. Replace `telemetry/simulators.py` with real collectors.
2. Swap `reasoning/engine.py` with your LLM inference (be mindful of the guardrails in `safety/guardrails.py`).
3. Implement a privileged applier for controlled hosts (not included here).

---

## License

Apache-2.0. See `LICENSE.md`.


---

## 🔒 Real `/proc/sys` Mode (Sysctl)

> **위험성 주의:** 실서버에서 커널 파라미터를 변경하면 시스템 안정성에 영향이 있을 수 있습니다.  
> 본 도구는 **화이트리스트 + 가드레일 + 백업/롤백**을 제공합니다. *반드시 단계적으로 적용하세요.*

### 드라이런(권장)
```bash
bash experiments/run_sysctl_dryrun.sh
# 또는
python -m semantos.cli --applier sysctl
```

### 실제 적용(루트 필요)
```bash
sudo -E bash experiments/run_sysctl_apply.sh
# 또는
sudo -E python -m semantos.cli --applier sysctl --apply
```

실제 적용 시:
- 변경 전 값을 `experiments/backup/sysctl_backup.json`에 저장합니다.
- 화이트리스트: `vm.dirty_*`, `vm.swappiness`, `net.core.{somaxconn,netdev_max_backlog}`, `kernel.{sched_latency_ns,sched_min_granularity_ns,numa_balancing}`
- 가드레일 위반 시 적용 중단

### 롤백(루트 필요)
```bash
sudo -E bash experiments/run_sysctl_rollback.sh
# 또는
sudo -E python -m semantos.cli --applier sysctl --rollback
```

---
