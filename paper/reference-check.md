# Reference check (2026-10-14)

All 67 entries of `reference-data.bib` (66 cited) were compared with their
official records by `scripts/check_references.py`: title, author surnames, year,
pages and venue against the ACL Anthology BibTeX (19 entries), Crossref (DOIs),
the arXiv API (preprints and model reports), OpenReview (ICLR, ICML and NeurIPS
papers linked through arXiv) and publisher landing pages (NeurIPS, PMLR, model
cards, kernel documentation). Every entry exists and every cited venue was
confirmed.

## Corrections made

| Entry | Problem | Fix |
|---|---|---|
| Herodotou2020Survey | year 2020; ACM CSUR 53(2) is the March 2021 issue (online April 2020) | year 2021 |
| Lin2025TuneAgent | "(first released as OS-R1)" inside the title | official arXiv title; the earlier name moved to the note |
| Ji2023HallucinationSurvey | no volume or pages; arXiv link | ACM CSUR 55(12):1-38, DOI link |
| Rashkin2023AIS | no pages; arXiv link | Computational Linguistics 49(4):777-840, Anthology link |
| Gao2023ALCE, Min2023FActScore | no pages; arXiv links | EMNLP 2023 pages 6465-6488 and 12076-12100, Anthology links |
| Shi2023Distracted, Mohri2024ConformalFactuality | no volume or pages; arXiv links | PMLR 202:31210-31227 and 235:36029-36047, PMLR links |
| Gibbs2021ACI | no pages | 1660-1672 (NeurIPS proceedings record) |
| Turpin2023Unfaithful | no volume | volume 36 |
| Snoek2012BO, Geifman2017Selective | page numbers not in the official NeurIPS records | pages removed; Geifman link updated to the current proceedings page |

## Flags checked and left as they are

- VanAken2017OtterTune, Bohnet2022AttributedQA: name particles ("Van Aken",
  "Baldini Soares") match the records.
- Qwen2024Qwen25, DeepSeek2025V32: cited with the team author, as the reports
  ask.
- Wang2023SelfConsistency, Kuhn2023SemanticUncertainty (ICLR 2023),
  Chen2020TabFact (ICLR 2020), Quach2024ConformalLM (ICLR 2024): confirmed on
  OpenReview by hand; the script's search returned the CoRR copy first.
- Herodotou2020Survey pages "43:1--43:37": ACM's article-number form of
  Crossref's 1-37.

## Re-run 2026-10-20 (pre-submission)

`refcheck.py` was run against the official records (ACL Anthology, Crossref,
arXiv, OpenReview and landing pages) for all 67 bib entries, 66 of them cited.
57 cited entries match exactly. The 9 flagged entries are the cases already
resolved above: name particles (Van Aken, Baldini Soares), team authors (Qwen,
DeepSeek-AI), ACM article-number pages (Herodotou), and ICLR papers whose
accepted OpenReview record the API search does not return (Wang 2023, Kuhn
2023, Chen 2020, Quach 2024; confirmed earlier on the venue pages). No new
discrepancy was found. LinuxVM is not cited, so it does not appear in the
bibliography.

## Added 2026-10-23

- Wallat2025Correctness: Crossref record 10.1145/3731120.3744592 (ICTIR 2025,
  pages 22-32; arXiv 2412.18004). Title, year and pages match; the only flag is
  the "de Rijke" surname particle.

## Re-run 2026-10-23 (final pre-submission)

All 68 bib entries (67 cited) were checked against their official records.
57 cited entries match exactly. The 10 flagged entries are the cases already
resolved above, and no new discrepancy was found:
- name particles: Van Aken, Baldini Soares, de Rijke;
- team authors: Qwen, DeepSeek-AI;
- ACM article-number pages: Herodotou;
- ICLR papers whose accepted record the OpenReview API search misses: Wang
  2023, Kuhn 2023, Chen 2020, Quach 2024.
