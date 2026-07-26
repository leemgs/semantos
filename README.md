# SemantOS

**Safe and Explainable Kernel Tuning via Semantic Reasoning and Guardrailed LLMs**

This repository accompanies the SemantOS paper. It is organized into three
top-level directories: the research **paper**, the reference **code**, and
sharing materials (**ppt**).

```
.
├── paper/   # AAAI-27 submission sources (LaTeX) and the built PDFs
├── code/    # SemantOS prototype: telemetry → KB → reasoner → safety runtime
└── ppt/     # Talk deck (Korean) and one-page poster (English) for sharing
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
| `Makefile` | Builds **both** PDFs below (`make`). |
| `main.pdf` | **Submission PDF** — 7 content pages + references; **0 embedded link annotations**. Upload this. |
| `main_bluelink.pdf` | **Debug PDF** — same content but reference URLs are blue clickable links, for pre-submission link checking only. **Not for submission.** |
| `README.txt` | Build instructions and the reference-URL modes. |
| `semantos_7p_aaai_20260705_2010.zip` | Self-contained supplementary/source archive (compliant `main.pdf` only). |

**Build:** `cd paper && make` — produces two files from the single source:

| Output | `\debugenablereferencelink` | Reference URLs | AAAI-27 |
|--------|------|------|---------|
| `main.pdf` | `0` (default) | hidden, no link annotations | ✅ compliant — **submit this** |
| `main_bluelink.pdf` | `1` | blue clickable links (debug) | ❌ do not submit |

A plain `pdflatex main.tex` also works and yields the compliant `main.pdf`
(the toggle defaults to `0`). The debug build is written to a *separate*
filename on purpose, so the submission file `main.pdf` is always the
link-free build.

**AAAI-27 compliance notes.** The author block is anonymized via the
`[submission]` option; the submission PDF (`main.pdf`) embeds no clickable
link annotations; and no part of the paper or supplement links to the authors'
own web material. Reference URLs point exclusively to pre-existing third-party
resources (ACM, NeurIPS, arXiv, IEEE, etc.).

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
| `reasoner/` | Graph-grounded reasoner; emits knob/value/rationale and calibrated uncertainty (`k=3` self-consistency). Serves the three loop endpoints `/get_recommendations`, `/apply`, `/log_outcome`. |
| `safety-runtime/` | Conformal threshold `τ`, staged rollout (canary → ramp → full), automatic rollback. |
| `operator-console/` | FastAPI console that surfaces telemetry, evidence, and suggestions with override/rollback controls. |
| `reproduce/` | Scripts and result CSVs/figures to reproduce the paper's experiments. |
| `proto/` | Typed control-message schema (`semantos-control.v1.yaml`). |
| `data/`, `workloads/` | Seed data and workload drivers. |
| `docker-compose.yml`, `docker-compose.ebpf.yml`, `Makefile` | One-command bring-up and reproduction targets. |

**Quick start:** `cd code && docker compose up` (see `code/README.md` and
`code/reproduce/README.md` for reproduction steps). The offline reproduction
harness regenerates every table, figure, and theory check with `python -m
reproduce.run_all` (34/34 checks pass against the paper's reported CIs).

---

## `./ppt/` — Sharing materials

Presentation and poster for sharing SemantOS with OS researchers and
practitioners. Both are generated from small [`pptxgenjs`](https://gitbrent.github.io/PptxGenJS/)
scripts and reuse a single navy/teal design system.

| Path | Description |
|------|-------------|
| `semantos_ko.pptx` | **Talk deck (Korean)** — 12 slides: motivation, architecture, semantic KB, safety runtime, theory, results, ablation/Pareto, user study, conclusion. |
| `semantos_poster_en.ppt` | **Poster (English)** — a single 48″×36″ landscape slide summarizing problem, method, guarantees, and results for a poster session. |
| `gen_ko.js` / `gen_poster.js` | Generator scripts (source of truth for the two artifacts). |

**Rebuild:** `cd ppt && npm install pptxgenjs && node gen_ko.js && node gen_poster.js`.
The poster is authored as `.pptx` and exported to legacy `.ppt` with LibreOffice
(`soffice --headless --convert-to ppt:"MS PowerPoint 97" semantos_poster_en.pptx`).
