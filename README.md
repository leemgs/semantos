# SemantOS

**Safe and Explainable Kernel Tuning via Semantic Reasoning and Guardrailed LLMs**

SemantOS treats Linux kernel tuning not as a black box but as a semantically
grounded control loop: it observes system telemetry, reasons over a knowledge
base of typed inter-knob dependencies with a guardrailed LLM, attaches an uncertainty estimate to every recommendation, and applies changes only
through a staged, auditable rollout with automatic rollback.

## Repository layout

| Folder | Contents |
|--------|----------|
| [`paper/`](paper/) | revised manuscript sources (LaTeX); stale compiled PDFs were withdrawn. |
| [`code/`](code/) | SemantOS prototype: telemetry → knowledge base → reasoner → safety runtime. |
| [`ppt/`](ppt/) | Sharing materials: a talk deck (Korean) and a one-page poster (English). |


> **Revision status (2026-09-25):** Previously checked-in simulated paper
> results have been withdrawn. The repository now requires independently
> collected raw hardware runs and makes no empirical or formal safety claim
> until those data pass the provenance-first protocol.
