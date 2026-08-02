# SemantOS

**Safe and Explainable Kernel Tuning via Semantic Reasoning and Guardrailed LLMs**

SemantOS treats Linux kernel tuning not as a black box but as a semantically
grounded control loop: it observes system telemetry, reasons over a knowledge
base of typed inter-knob dependencies with a guardrailed LLM, attaches a
calibrated uncertainty to every recommendation, and applies changes only
through a staged, auditable rollout with automatic rollback.

## Repository layout

| Folder | Contents |
|--------|----------|
| [`paper/`](paper/) | AAAI-27 submission sources (LaTeX) and the built PDF. |
| [`code/`](code/) | SemantOS prototype: telemetry → knowledge base → reasoner → safety runtime. |
| [`ppt/`](ppt/) | Sharing materials: a talk deck (Korean) and a one-page poster (English). |
