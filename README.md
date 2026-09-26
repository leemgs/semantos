# SemantOS

Research prototype for knowledge-grounded kernel-tuning proposals and independent
bundle gating. The REST runtime is **dry-run only**. A separate bounded experiment
applies and restores timer slack and affinity in owned child threads; it does not
establish production deployment safety.

The measured evidence comprises raw local baseline measurements, a 9,600-event
per-process kernel experiment, and a prospective role-separated follow-up with
8,000 grid events and 80 staged executions. No tuning gain is claimed.

| Path | Contents |
|---|---|
| [paper/](paper/) | Manuscript sources and built PDFs |
| [code/](code/) | Prototype, regression tests and measurement tools |
| [code/evaluation/results/local-2026-09-26/](code/evaluation/results/local-2026-09-26/) | 3,000 measured operations, environment, hashes and statistics |
| [Kernel experiment](code/evaluation/results/kernel-local-2026-09-26/summary.md) | Per-process timer-slack/affinity interventions |
| [Controlled follow-up](code/evaluation/results/controlled-2026-09-26/summary.md) | Frozen selectors, gate confusion counts, real restoration and source lineage |
| [Model audit status](code/evaluation/results/model-audit-2026-09-26/status.json) | Recorded backend failure; no LLM or faithfulness result |

Training selected the baseline configuration in both kernel experiments; no
selected-policy gain was observed. The LLM's incremental value and explanation
faithfulness remain unverified.
