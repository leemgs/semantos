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
| [Model audit](code/evaluation/results/model-audit-summary/summary.md) | Four local models (Qwen2.5-7B/14B, Llama-3.1-8B, Phi-4) and three hosted ones (Llama-3.3-70B, Qwen3-235B, DeepSeek-V3.2) on the frozen follow-up evidence, held-out replay, deletion controls and a manual claim check |
| [Earlier audit attempt](code/evaluation/results/model-audit-2026-09-26/status.json) | Recorded backend failure (kept as history) |

Training selected the baseline configuration in both kernel experiments; no
selected-policy gain was observed. Seven LLMs from 7B to 685B parameters given the same frozen evidence did not
improve on the default either: all but Llama-3.1-8B chose it, Llama-3.1-8B chose
a configuration that is worse on held-out replay, and many quantitative
explanation claims misstate the evidence despite valid citations (16 of 28 for
the local models, 9 of 27 for the hosted full-context explanations). Explanation
faithfulness remains unestablished.
