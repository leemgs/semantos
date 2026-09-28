SemantOS paper sources
======================
Target venue: ACL 2027 (ACL Rolling Review), long paper, anonymous review mode.
`make` builds main.pdf from main.tex with the official ACL style files
(acl.sty, acl_natbib.bst from github.com/acl-org/acl-style-files). Reference
URLs are clickable. The unnumbered Limitations section (required) and Ethics
Statement follow the Conclusion and do not count toward the 8-page limit.

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

Current PDF: 11 pages (body ends on page 8; Limitations and Ethics Statement
on pages 8-9; references on pages 9-11).
