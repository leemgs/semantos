SemantOS paper sources
======================
`make` builds main.pdf and main_bluelink.pdf from main.tex.
main.pdf omits reference-link annotations (upload this one);
main_bluelink.pdf shows clickable reference URLs for link checking only.

Measured evidence used by the paper (paths under ../code/evaluation/results/):
- local-2026-09-26/: 3,000 baseline operations (local-measurements.tex).
- kernel-local-2026-09-26/: 9,600 timer-slack/affinity events (kernel-measurements.tex).
- controlled-2026-09-26/: 8,000 grid events, frozen selection and gate, split
  lineage, 80 staged child executions with restoration (controlled-measurements.tex
  is copied from that directory's generated table.tex).
The matching analyze*.py scripts verify hashes and regenerate the tables.

Figures: Figure 1 (decision path) is TikZ inside 040-design.tex. Figure 2,
figures/gate_replay.pdf, is regenerated from the raw controlled log by
  python3 ../code/evaluation/plot_gate_replay.py --out figures/gate_replay.pdf
which re-runs the hash/lineage checks and asserts its counts match analysis.json.

The follow-up covers one workload family on one host. Selector comparisons are
paired offline replay. The model audit failed before inference; its status is
stored under results/model-audit-2026-09-26/. No LLM-superiority,
explanation-faithfulness or production-safety result is claimed.

Current PDF: 8 pages (body ends on page 7; references on pages 7-8).
