# SemantOS

Research prototype for knowledge-grounded kernel-tuning proposals and independent
bundle gating. The current runtime is **dry-run only**; it does not write kernel
settings or establish deployment safety.

The rejected version's target-matching simulations are quarantined, not used as
performance evidence. The revised manuscript includes new raw local baseline
measurements, 9,600 actual kernel-intervention timing events, and a controlled evaluation protocol; it does not claim tuning gains.

| Path | Contents |
|---|---|
| [paper/](paper/) | Revised manuscript and rebuilt PDFs |
| [code/](code/) | Prototype, regression tests and real measurement tools |
| [code/evaluation/results/local-2026-09-26/](code/evaluation/results/local-2026-09-26/) | 3,000 measured operations, environment, hashes and statistics |
| [REVIEW_RESPONSE.md](REVIEW_RESPONSE.md) | Review-by-review changes, validation and remaining access needs |
| [archive/](archive/) / [code/legacy/](code/legacy/) | Historical rejected artifacts; not current evidence |

The per-process timer-slack/affinity experiment is in [kernel-local-2026-09-26](code/evaluation/results/kernel-local-2026-09-26/summary.md). Training selected the baseline configuration at both wake-up intervals; no selected-policy gain was observed.

The manuscript also includes separately supplied, author-confirmed hardware results in `paper/110-reported-results.tex`. Their reported 14% aggregate P95 reduction is preserved with explicit aggregation discrepancies and missing run-level provenance; it is not a result of the local measurements.
