# `reproduce/` — offline paper reproduction

Regenerates every SemantOS table/figure from a single seeded harness. No Docker,
no Neo4j, no LLM — pure `numpy`/`scipy`/`matplotlib`.

```bash
python -m reproduce.run_all     # tables/figures data + PASS/FAIL vs paper
python -m reproduce.figures     # render PNGs from the result CSVs
```

## Module map

| File | Role |
|------|------|
| `spec.py`         | Single source of truth: knobs, 6 workloads, 3 servers, and all paper targets (`PAPER_*`), global seed, default τ, α, cost weights. |
| `depgraph.py`     | Typed/signed inter-knob dependency graph; `induce_edges()` runs the pairwise co-tuning sweep that yields the Figure-1 synergy. |
| `conformal.py`    | Split-conformal veto threshold, cost-based τ selection `C(τ)`, precision/recall, Prop. 1 bound, Thm. 1 decomposition, sliding-window recalibration. |
| `adwin.py`        | O(n)-per-update ADWIN drift detector. |
| `calibration.py`  | Fitted score mixture (`BETA_SAFE`/`BETA_UNSAFE`) and helpers that make the τ-sweep and anomaly mapping match the paper. |
| `response_model.py` | Calibrated per-workload response profiles used for Tables 2/3 and Figures 1/3. |
| `controllers.py`  | Controller/ablation registries and `SemantOSLoop` (Algorithm 1) for the drift study and theory checks. |
| `run_all.py`      | Orchestrates everything; writes CSVs to `results/` and prints the PASS/FAIL report. |
| `figures.py`      | Renders `fig1_knob_synergy.png`, `fig3_pareto.png`, `tau_sweep.png`, `drift_study.png`. |

## What each check maps to

- **Table 2** — median/P95/anomaly reductions vs baseline; operator-time saving.
- **Table 3** — full vs `wo_depgraph` / `wo_rag` / `wo_safety` / `kb_only`.
- **Figure 1** — single-knob vs joint tail-latency effect (super-additivity).
- **Figure 3** — anomaly/P95 Pareto frontier and the gain vs the Expert point.
- **τ-sweep** — rollback precision/recall/anomaly at τ ∈ {0.30, 0.55, 0.70} and
  the cost-selected τ\*.
- **Exploration** — configs explored vs BO/RL (speedup band).
- **Drift study** — 30 days, averaged over runs: anomaly < 3%, precision > 0.85.
- **Theory** — Thm. 1 expected-cost bound holds; Prop. 1 coverage recovers
  (realized α′ ≤ α + 1/(m+1) + ε).

## Determinism

All randomness derives from `spec.GLOBAL_SEED`. Tolerances in `run_all.py` are
set to the paper's reported confidence intervals, so a PASS means the harness
lands inside the paper's stated uncertainty — not that it merely trends the same
way.
