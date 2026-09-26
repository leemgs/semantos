# SemantOS

Research prototype for knowledge-grounded kernel-tuning proposals and independent
bundle gating. The REST runtime is **dry-run only**. A separate bounded experiment
applies and restores timer slack and affinity in owned child threads; it does not
establish production deployment safety.

The rejected version's target-matching simulations are quarantined, not used as
performance evidence. The revised manuscript includes new raw local baseline
measurements, an initial 9,600-event kernel experiment, and a prospective follow-up
with 8,000 grid events and 80 staged executions. It does not claim tuning gains.

| Path | Contents |
|---|---|
| [paper/](paper/) | Revised manuscript and rebuilt PDFs |
| [code/](code/) | Prototype, regression tests and real measurement tools |
| [code/evaluation/results/local-2026-09-26/](code/evaluation/results/local-2026-09-26/) | 3,000 measured operations, environment, hashes and statistics |
| [Controlled follow-up](code/evaluation/results/controlled-2026-09-26/summary.md) | Frozen selectors, gate confusion counts, real restoration and source lineage |
| [Model audit status](code/evaluation/results/model-audit-2026-09-26/status.json) | Recorded backend failure; no LLM or faithfulness result |
| [REVIEW_RESPONSE.md](REVIEW_RESPONSE.md) | Review-by-review changes, validation and remaining access needs |
| [archive/](archive/) / [code/legacy/](code/legacy/) | Historical rejected artifacts; not current evidence |

The per-process timer-slack/affinity experiment is in [kernel-local-2026-09-26](code/evaluation/results/kernel-local-2026-09-26/summary.md). Training selected the baseline configuration at both wake-up intervals; no selected-policy gain was observed.

The manuscript preserves separately supplied, author-confirmed hardware summaries
in `paper/110-reported-results.tex`. Their unresolved aggregation and missing raw
logs exclude them from the comparative conclusions. The LLM's incremental value
and explanation faithfulness remain unverified.
