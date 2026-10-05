# ARR submission form — draft fields

Plain-text versions of the fields asked for on OpenReview, taken from the
current paper. Paste them into the form; the chosen area and keywords are
suggestions.

## Title

Cited but Not Correct: Auditing Evidence-Grounded LLM Configuration Advice against Equally Informed Baselines

## Abstract (200 words, plain text)

Language models increasingly recommend actions and justify them with citations to evidence in the prompt. Such a rationale makes three promises: the action is good, its claims about the evidence are true, and the decision rests on what is cited. Evaluations rarely test all three, or compare against what the evidence alone would recommend. Our audit protocol gives an equally informed non-LLM selector the same frozen evidence, ablates and deletes evidence, verifies every quantitative claim in an explanation against it, and scores decisions on independently labeled held-out outcomes. We apply it to configuration advice on real Linux kernel interventions with GroundKern, a testbed separating evidence, proposals and enforcement, and ten LLMs from 7B to frontier scale. The promises come apart. Evidence is necessary: without it, nine models mostly choose worse. It is also sufficient: with it, nine reproduce a table-lookup selector and none improves on it. Citations are valid but one-sided: 252 of 260 cited runs belong to the chosen configuration. Explanations are cited but not correct: 41 of 97 audited claims misstate the evidence, mostly alongside a correct decision, and deletion reveals citation-specific reliance for only one model. Prompts, responses, annotations, code and logs are provided as supplementary material.

## TL;DR

LLM configuration advice that cites valid evidence is no better than a selector
that reads the same evidence, cites it one-sidedly, and misstates it in 41 of
97 audited claims; we propose an audit protocol that measures these gaps.

## Keywords

attribution; grounded generation; explanation faithfulness; citation
evaluation; claim verification; LLM evaluation; decision support;
retrieval-augmented generation

## Suggested area (choose one)

1. Interpretability and Analysis of Models for NLP — explanation correctness,
   citation behavior and reliance tests are the core findings.
2. Resources and Evaluation — if the audit protocol and released annotations
   are to be emphasized.
3. NLP Applications — if the configuration-advice setting is to be emphasized.

## Contribution types (check the matching boxes)

- Model analysis & interpretability
- Data analysis / evaluation methodology
- Software and data: provided as supplementary material (anonymized zip)

## Languages studied

English

## Paper type

Long paper (8 pages + unlimited references, Limitations, Ethics Statement and
appendix).

## Previous submission

The ARR form asks only about earlier ARR submissions. The work was previously
submitted to AAAI-27 under a different, systems-oriented framing; ARR does not
require reporting submissions to non-ARR venues. **[저자 확인]** Check the
current cycle's call for papers in case it asks about this.

## Software / data upload

Upload the zip built by
`python3 scripts/make_anonymous_release.py --out <dir> --zip` from the final
commit as supplementary software and data.
