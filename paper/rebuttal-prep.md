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
- Done: a second annotator who is not an author labeled all 97 claims blind
  (without drafted labels or checks): Cohen's kappa 0.918 over seven labels,
  0.914 for misstated vs not. All five disagreements are claims the second
  annotator judged correct (three "significantly lower", one partly wrong,
  one cited range); with the second annotator's labels the misstated count is
  37/97 instead of 41/97, so the conclusion does not depend on who labels.
- Done: a third, independent blind annotator (not an author): kappa 0.856 /
  0.808 with the verified labels; Fleiss' kappa 0.847 over all three; the
  majority label equals the verified label for all 97 claims; misstated count
  38/97. Five of its nine disagreements read "(runs 0-5)" as restricting "all
  retrieval runs"; two came from a blind-sheet error (rows 48, 53 showed a
  sentence from another seed), now fixed and disclosed in Appendix C.
- Also: the rule check decides 56 of 97 labels and agrees with all; a mutation
  test detects 76 of 97 flipped labels.

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
- Done (Appendix E): hosted models rerun with a paraphrased prompt, reversed
  and shuffled evidence, no citation cap and temperature 0.7. Decisions
  (180/180 across all conditions incl. the original) and one-sided citation
  (100% of cited runs in every new condition) do not change; the quantifier
  overstatement proxy fires in 9-21 of 30 explanations per condition.
- Open: verified claim labels for the new answers; local models.

## 6. "The citation position effect is confounded by the six-citation cap."

- Tested (§5.2, Appendix E): with the runs reversed, four of six hosted
  models cite the runs listed first (88/138 in the first half of the list,
  50/138 from blocks 0-4); without the cap they cite 9.0 runs per answer. So
  the prefix comes from the cap plus list position, and the paper now says so;
  one-sidedness does not depend on the cap (256/256).

## 7. "Deletion was non-estimable for half the models."

- Done (Appendix I): with the table split into per-configuration items and
  configuration-matched controls, the test is estimable for 32 (A) and 35 (B)
  seeds. No hosted model changes under either deletion; only bf16
  Llama-3.1-8B switches under cited deletion alone (5/5). Splitting the table
  also flipped that model's full-context choice to the control. Conceded:
  reliance under deletion is rare and unstable across precision and format,
  and controls still differ in which blocks remain.

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

- Done (Appendix C, Table 9; §6). Eight judges (three NLI cross-encoders,
  Flan-T5-large, AlignScore-large and three MiniCheck models), given the cited
  items as premise, reach balanced accuracy 0.47–0.68 against the verified
  labels; with all 42 evidence items as premise, MiniCheck stays at 0.49-0.52. Lenient judges
  accept up to half of the wrong values (11/22); strict judges reject nearly
  all overstatements but also most correct claims (RoBERTa accepts 4/51).
  At least one judge accepts 28 of the 41 misstated claims.
- TRUE (T5-11B) did not fit the 15 GB CPU container; offer it for the
  camera-ready if asked.

## 11b. "So how would you fix it?"

- Done (§5.3, Appendix F): verify instruction, precomputed summary statistics
  and both, on the six hosted models (90 answers, 0.70 USD). Flagged
  quantifiers 21 -> 1 / 4 / 0 of 30, range errors 7 -> 2 / 0 / 0; decisions
  unchanged. The automatic checks match the verified labels on the original
  answers (range check: exactly the 7 explanations with a verified wrong
  range), but see only two error types; reading the explanations found
  residual false comparisons. Open: verified labels for the 90 explanations
  (`results/mitigation-baseline/explanations-for-review.csv`).

## 11c. "Would reasoning models get it right?"

- Done (§5.3, Appendix G): within-model toggles for four hosted models.
  Decisions unchanged, no contrary citations; DeepSeek-V3.2 (reasoning on) and
  the Qwen3 thinking variant still flag the "consistently lowest"
  overstatement in 4/5 and 5/5 explanations; Nemotron with reasoning flags
  fewer (2 and 1 of 5) but writes half-length explanations. Note: both
  Gemini models already reasoned by default in the main audit (~490 and
  ~1,100 reasoning tokens). Automatic checks only.

## 11d. "Are the local results a quantization artifact?"

- Done (Appendix H): bf16 reruns of Llama-3.1-8B and Phi-4 (providers that
  declare bf16) and an 8-bit rerun of Qwen2.5-7B reproduce every evidence and
  no-evidence decision, including Llama's wrong choice, and the explanation
  errors recur. Qwen2.5-14B has no full-precision endpoint.
- Conceded: Phi-4's citation-specific reliance (the only such case) does not
  survive: with bf16 weights it cites the same runs but keeps the control
  when they are deleted. The abstract, §5.4 and conclusion now say so; the
  difference may come from precision or from the serving stack.

## 12. "Who decided what counts as a claim?"

- Conceded (Limitations, Annotation): the blind annotators labeled claims that
  had already been extracted; extraction was not independently validated, and
  only quantitative or comparative claims were audited.
- Offer: an independent annotator segments the 50 full-context explanations
  from scratch; report claim-level recall/precision of the extraction and the
  misstated count on the union of claims.

## 13. "Is the gate failure statistically meaningful?"

- Stated precisely in §5.5: unsafe acceptance (5/25, 4/24) is significantly
  above 5% for this calibration draw (one-sided binomial p = .007, .03) but
  within sampling error of 10% (p = .10, .21). The bound is marginal over
  calibration draws, so one draw is a single realization.
- Offer: repeat calibration/test over additional period pairs.

## 14. "Does a misstated rationale actually mislead people?"

- Not measured; the paper claims only that the rationale misstates checkable
  facts, not that readers are misled.
- Prepared: a between-subjects study protocol, ready for pre-registration (misstated vs. minimally
  corrected vs. no rationale; six verbatim stimuli; six evidence probes;
  60 per arm for power ≈ .85 under stated assumptions), with consent template,
  static and online instruments and analysis script (`paper/human-study/`,
  `human_study.py`). Needs ethics approval and recruitment before it can run;
  report results only after real data exist.

## 15. "One evidence list is one data point."

- Appendix J reruns the six hosted models on three further instances from
  training-side data: 4 ms calibration runs as retrieval items, permuted labels
  and a second measurement session (90 calls, 0.45 USD).
- Choices follow the evidence under permuted labels (30/30).
- When the 4 ms runs compete with the table, Llama-3.3-70B leaves the table
  choice in all five seeds, so sufficiency is qualified.
- One-sided citation persists (only Gemini Flash cites competitors), and the
  quantifier proxy fires in 13-18 of 30 explanations per instance.
- These are automatic checks; an author should verify
  `results/evidence-instances/explanations-for-review.csv` before the response.
- Still the same host and workload family; another domain remains open.

## 16. "Only one domain."

- Appendix K adds SQLite settings (synchronous × journal mode), measured for
  this paper with training, retrieval and test roles. The data were committed
  before any model call.
- The table favours OFF/WAL, the runs favour NORMAL/WAL (8/10 blocks), and the
  test favours OFF/WAL (7/10 blocks; paired +20.6 ± 26.7 %, not significant).
- Choices: 21/27 evidence answers follow the runs; without evidence 25/30
  choose OFF/WAL.
- Explanations: 13/27 contain a misstatement on an AI-assisted reading, 9 of
  which misreport the training table as agreeing with the choice. Selective
  citation persists.
- To do before the response: an author or annotator verifies
  `explanations-read.csv`. A third domain with textual evidence remains open.

## 17. "The headline claims are domain-specific."

- Agreed, and now stated: the abstract, introduction and conclusion scope
  necessity and sufficiency to the kernel task. In the database task
  (Appendix K), the evidence moves choices away from the selector, and
  explanations misreport contrary evidence.

## Quick additions possible during the response period (no new hardware runs)

1. Adjudication of the disagreements, if asked.
2. TRUE (T5-11B) or an LLM judge on the existing claims.
3. Verified claim labels for the robustness answers (Appendix E).

Done since the first draft: results by scale and family (Appendix D), prompt,
order, cap and decoding robustness (Appendix E, 0.83 USD), and four more
attribution judges (Appendix C).
