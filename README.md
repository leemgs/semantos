# SemantOS

**Safe and Explainable Kernel Tuning via Semantic Reasoning and Guardrailed LLMs**

This repository accompanies the SemantOS paper. It is organized into two
top-level directories: the research **paper** and the reference **code**.

```
.
├── paper/   # AAAI-27 submission sources (LaTeX) and the built PDF
└── code/    # SemantOS prototype: telemetry → KB → reasoner → safety runtime
```

---

## `./paper/` — Paper sources (AAAI-27 Main Technical Track)

Double-blind LaTeX sources built on the official AAAI-27 Author Kit
(`aaai2027.sty` / `aaai2027.bst`, unmodified) plus the compiled PDF.

| Path | Description |
|------|-------------|
| `main.tex` | Master document; `\input`s each numbered section. |
| `000-title.tex` … `100-conclusion.tex` | Section files (title, abstract, introduction, background, motivation, design, evaluation, discussion, ethics, conclusion). |
| `reference-data.bib` | Bibliography (references to pre-existing, third-party resources only). |
| `aaai2027.sty` / `aaai2027.bst` / `aaai2027.bib` | Official AAAI-27 Author Kit files (unmodified). |
| `figures/` | Architecture, pairwise-effects, and Pareto-frontier figures. |
| `main.pdf` | Compiled submission PDF (7 content pages + references; **0 embedded link annotations**). |
| `README.txt` | Build instructions and the reference-URL review toggle. |
| `semantos_7p_aaai_20260705_2010.zip` | Self-contained supplementary/source archive. |

**Build:** `pdflatex main` → `bibtex main` → `pdflatex main` → `pdflatex main`

**AAAI-27 compliance notes.** The author block is anonymized via the
`[submission]` option; the reference-URL toggle in `main.tex` never emits
clickable link annotations (toggle `0` hides URLs for submission, toggle `1`
prints them as plain, non-clickable text for author review only); and no part
of the paper or supplement links to the authors' own web material. Reference
URLs point exclusively to pre-existing third-party resources (ACM, NeurIPS,
arXiv, IEEE, etc.).

---

## `./code/` — Reference prototype

A lightweight, containerized **semantic OS tuning** stack that closes the loop
between telemetry, a graph-backed knowledge base, an LLM reasoner, and a safety
runtime. Intended for local experimentation, demos, and reproducible
benchmarks — not production hardening. See `code/README.md` for full details.

| Path | Role |
|------|------|
| `telemetry-agent/` | Collects kernel/system signals (psutil, eBPF-style) — p95 latency, syscall rate, anomaly indicators. |
| `kb/`, `kb-service/` | Knowledge base: typed/signed dependency edges (Neo4j) with γ-decay, plus FAISS vector retrieval (RAG). |
| `reasoner/` | Graph-grounded reasoner; emits knob/value/rationale and calibrated uncertainty (`k=3` self-consistency). |
| `safety-runtime/` | Conformal threshold `τ`, staged rollout (canary → ramp → full), automatic rollback. |
| `operator-console/` | FastAPI console that surfaces telemetry, evidence, and suggestions with override/rollback controls. |
| `reproduce/` | Scripts and result CSVs/figures to reproduce the paper's experiments. |
| `proto/` | Typed control-message schema (`semantos-control.v1.yaml`). |
| `data/`, `workloads/` | Seed data and workload drivers. |
| `docker-compose.yml`, `docker-compose.ebpf.yml`, `Makefile` | One-command bring-up and reproduction targets. |

**Quick start:** `cd code && docker compose up` (see `code/README.md` and
`code/reproduce/README.md` for reproduction steps).
