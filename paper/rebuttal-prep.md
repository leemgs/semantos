# Rebuttal preparation (internal; not part of the submission)

Likely reviewer concerns and answers grounded in the paper and its data. Each
answer points to where the evidence is, so it can be adapted to the actual
reviews. Keep rebuttals factual: concede what the paper concedes in its
Limitations and offer concrete additions for the camera-ready version.

## 1. "The task is tiny and the default is optimal, so the LLMs could never win."

- This is deliberate and stated (§1 last paragraph, Limitations "Task and
  generality"). The paper audits failure modes; it does not claim LLMs cannot
  add value.
- The citation and explanation findings do not depend on the default being
  optimal: 35 of the 41 misstated claims accompany a *correct* decision
  (§5.3), and one-sided citation (252/260) occurs regardless of which
  configuration wins.
- The protocol is task-agnostic (ARTIFACTS.md §4). Offer: in the camera-ready,
  add a task where the default is not optimal, or clarify the scope in the
  title/abstract if the reviewers prefer.

## 2. "The claim labels come from an AI assistant and a single author."

- Disclosed in §4, Limitations, Ethics and Appendix C.
- Mitigations already in the paper: a rule-based check decides 56 of 97 labels
  directly from the evidence and agrees with all of them; a mutation test
  detects 76 of 97 flipped labels; every label is supplied with its check.
- Most claims are factual checks of numbers against a small table (e.g.,
  "ranges from 85.0 to 430.7" vs. a maximum of 571.84), where disagreement is
  unlikely.
- Offer: add a second, independent annotator for all 97 claims in the
  camera-ready and report Cohen's kappa (`claim_review_agreement.py` is ready).

## 3. "Why is kernel tuning an ACL paper?"

- The object of study is the LLM rationale: decision, citations, claims and
  reliance (§1, §4 Table 1). Configuration advice is the testbed because its
  evidence is structured and exactly checkable and its outcomes are measured
  independently (§1 second paragraph).
- The findings speak to attribution evaluation (ALCE/AIS), data-to-text
  accuracy and faithfulness research (§2, §6).

## 4. "Novelty over ALCE / AIS / FActScore?"

- Those evaluate whether statements are supported by citations. This paper
  adds (i) a decision-level baseline that receives the same evidence, (ii) an
  analysis of *which* evidence is cited (one-sided and front-loaded
  citations, invisible to per-citation support scores, §6), (iii) exact
  claim checking against structured evidence, and (iv) matched deletion for
  reliance.

## 5. "Greedy decoding, one prompt, five seeds: results may be prompt-specific."

- Conceded in Limitations ("Models and prompting").
- The error types recur across ten models from six families and a wide range of scales
  (§6 "Scale does not remove the error types").
- Offer: a prompt-variation and sampling study (temperature > 0, reworded
  instructions, shuffled evidence order) for the camera-ready; shuffled
  evidence order would also test the position effect directly.

## 6. "The citation position effect is confounded by the six-citation cap."

- Conceded (§5.2, Limitations). The cap explains selecting few items, not
  selecting items of the chosen configuration (252/260) or the earliest ones.
- Offer: rerun with shuffled evidence order and with no cap.

## 7. "Deletion was non-estimable for half the models."

- Reported as a finding about the method (§5.4, §6): matched deletion needs
  redundant same-kind evidence. Offer: duplicate the training-table item in
  split form so every cited item has a matched control.

## 8. "Hosted models are not reproducible."

- Records keep each prompt and hash, the raw response, the routed provider
  and fingerprint (Appendix C). Local models are hashed GGUF files.
  `reproduce_paper.py` regenerates every number from these records.

## 9. "Is 41/97 statistically meaningful?"

- Appendix C gives 95% Wilson intervals: 42% (33–52%) overall, 57% (39–73%)
  local, 36% (26–48%) hosted, and notes that repeated hosted claims make the
  intervals optimistic. The point is that misstatement is common at every
  scale, not a precise rate.

## 10. "The risk-gate section is off-topic."

- It illustrates the same lesson for a numeric confidence signal: nominal
  calibration fails under a period shift (§5.5). Offer: shorten it further or
  move it to the appendix to make room for requested additions.

## 11. "Would an entailment-based attribution judge catch these errors?"

- Stated as an open question (§6). Offer: run an NLI/AlignScore-style judge
  on the 97 claims against their cited items and report how many misstated
  claims it accepts; the labeled claims make this a ready benchmark.

## Quick additions possible during the response period (no new hardware runs)

1. Second annotator for the 97 claims, with kappa.
2. Entailment-judge experiment on the existing claims and evidence.
3. Re-analysis of existing records by model family and size.

Additions that need new model calls (API budget is small, about 0.5 USD for
the original hosted runs): prompt variants, shuffled evidence order, no
citation cap, temperature sampling.
