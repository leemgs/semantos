SemantOS — research revision after review
========================================
make builds main.pdf and main_bluelink.pdf from the same revised text.
main.pdf omits reference-link annotations; main_bluelink.pdf is for link checking.
This is a research draft, not a declaration of conference eligibility/compliance.

The revision withdraws unverified historical numerical claims. Measured evidence:
- results/local-2026-09-26/: 3,000 baseline operations.
- results/kernel-local-2026-09-26/: initial 9,600 timer/affinity events.
- results/controlled-2026-09-26/: 8,000 grid events, frozen selection and gate,
  declared split lineage, 80 actual staged child executions and restoration.
All result paths above are under ../code/evaluation/. Corresponding analyze*.py
scripts validate hashes and regenerate tables. controlled-measurements.tex is
copied from the follow-up's generated table.tex.

The follow-up is within one workload family and host. Selector comparisons are
paired offline replay, not live LLM optimization. A model audit was attempted but
blocked before inference; its failure is stored under results/model-audit-2026-09-26/.
No LLM superiority, explanation-faithfulness or production-safety result is asserted.
Author-supplied aggregates remain in an appendix with unresolved provenance and
aggregation; they are excluded from comparative conclusions.

Current PDF: 9 pages, including references and the author-reported appendix.

Original PDFs, supplementary ZIP, and the obsolete compliance report are under
../archive/rejected-2026-09-25/. Original source is retained in Git at 25ec0ca.
A current source/code/raw-data archive can be built with ../code/evaluation/package_revision.py.
It is a working research artifact, not an automatically anonymized submission.
