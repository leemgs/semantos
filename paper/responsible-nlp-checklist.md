# ARR Responsible NLP Checklist — draft answers

Draft for the ACL 2027 (ARR) submission *Cited but Not Correct: Auditing
Evidence-Grounded LLM Configuration Advice against Equally Informed Baselines*.
Section numbers refer to the current `paper/main.pdf`:
§1 Introduction, §2 Related Work, §3 Testbed, §4 Audit Protocol,
§5 Results (§5.1 decisions, §5.2 citations, §5.3 explanations, §5.4 reliance,
§5.5 gate), §6 Discussion, §7 Conclusion, Limitations, Ethics Statement,
Appendix A (testbed details), B (additional measurements), C (prompt and schema).

Answers are written in English so they can be pasted into the ARR form.
Lines marked **[확인 필요]** need a decision or a fact check by the authors
before submission.

---

## A. For every submission

**A1. Did you describe the limitations of your work?**
Yes. The unnumbered Limitations section covers task and generality (one task,
English prompts, small numeric evidence, opaque labels), annotation (single
annotator, 97 claims), models and prompting (one prompt, no decoding or
formatting variation, quantized local weights, non-reproducible hosted
serving, citation cap confounding the position effect), reliance measurement,
measurement scope and system/safety scope.

**A2. Did you discuss any potential risks of your work?**
Yes. Ethics Statement and Limitations. The main risks are (i) over-trust in
LLM rationales that cite valid evidence but misstate it, which the paper
measures and warns about (§5.3, §6); and (ii) harm from acting on
configuration advice. The REST runtime is a dry run, the actuator changes only
an owned child thread's timer slack and affinity and restores both, and no
host-wide setting is written; the paper makes no production-safety claim and
states that broader interventions need an isolated testbed and authorization.

---

## B. Did you use or create scientific artifacts?

Yes. We use pretrained LLMs and open-source software, and we create a
measurement dataset (8,000 wake-up events and further baseline logs), LLM
prompts and raw responses, per-claim annotations, and analysis code.

**B1. Did you cite the creators of artifacts you used?**
Yes. All ten models are cited where they are introduced (§4, Decisions
paragraph): Qwen2.5 7B/14B, Llama-3.1-8B, Phi-4, Llama-3.3-70B,
Qwen3-235B-A22B, DeepSeek-V3.2, Nemotron-3-Ultra-550B, Gemini 3.8 Flash and
Gemini 3.1 Pro preview. Linux interfaces are cited in §3/Appendix A.
llama.cpp and OpenRouter are cited with footnote URLs at their first mention
(§4), and llama-cpp-python with its URL and version in Appendix C.

**B2. Did you discuss the license or terms for use and/or distribution of any
artifacts?**
Partially — add the following to the camera-ready appendix or the release
README. All open-weight licenses below were checked against the Hugging Face
model cards on 2026-10-01.
- Qwen2.5-7B-Instruct, Qwen2.5-14B-Instruct: Apache 2.0.
- Qwen3-235B-A22B-Instruct-2507: Apache 2.0.
- Llama-3.1-8B-Instruct, Llama-3.3-70B-Instruct: Llama 3.1 / Llama 3.3
  Community License (`llama3.1`, `llama3.3`).
- Phi-4: MIT.
- DeepSeek-V3.2 (`deepseek-ai/DeepSeek-V3.2`): MIT, per the Hugging Face
  model card and its LICENSE file (checked 2026-10-01).
- Nemotron-3-Ultra-550B-A55B (`nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16`):
  OpenMDW License Agreement 1.1, a permissive license that requires keeping the
  agreement and notices when redistributing the model materials and imposes no
  restrictions on outputs (model card and license text checked 2026-10-01).
  OpenRouter's model list maps both API model IDs used in the audit to these
  Hugging Face repositories.
- Gemini 3.8 Flash, Gemini 3.1 Pro preview: proprietary, accessed under the
  Google/OpenRouter API terms of service.
- llama-cpp-python 0.3.35 and llama.cpp: MIT.
- Released artifacts (code, measurements, prompts, responses, annotations):
  Apache License 2.0 (`LICENSE` at the repository root). The bundled ACL style
  files keep their own terms (`acl_natbib.bst`: LaTeX Project Public License),
  and stored model responses remain subject to each model's license and
  provider terms; both exceptions are listed in the README.
  Redistribution of the hosted-model responses was checked on 2026-10-01:
  OpenRouter's Terms of Service (last updated 2026-08-31, §4 and §5) impose no
  restriction of their own on Outputs and defer ownership and use of Outputs
  to each model's Model Terms. For Gemini 3.8 Flash and Gemini 3.1 Pro preview
  these are Google's Gemini API Additional Terms (last updated 2026-04-28):
  Google does not claim ownership of generated content, users are responsible
  for their use of it and for its use by anyone they share it with, and the
  Services may not be used to develop competing models. The other hosted
  models' Model Terms are their open-weight licenses (Llama 3.3 Community
  License, Apache 2.0, MIT, OpenMDW-1.1), none of which restricts sharing
  outputs. Releasing the responses as research data is therefore permitted.

**B3. Did you discuss if your use of existing artifacts was consistent with
their intended use?**
Yes. All models are used for research inference only, through
their published weights or official/aggregator APIs, without fine-tuning or
redistribution of weights. The released data contain model outputs, not
weights. The Ethics Statement says so explicitly ("All models were used for research
inference under their licenses").

**B4. Did you discuss the steps taken to check whether the data that was
collected/used contains any information that names or uniquely identifies
individual people or offensive content?**
Yes / not applicable. The data are kernel timing measurements, synthetic
configuration labels and model responses to a fixed technical prompt; they
contain no personal data (Ethics Statement). The audited explanations are short technical texts about latency
measurements (listed in `paper/claim-review-explanations.md`).

**B5. Did you provide documentation of the artifacts, e.g., coverage of
domains, languages, and linguistic phenomena, demographic groups represented?**
Yes. §4 and Appendices B–C document the task, data roles, evidence format,
prompt and schema; `code/evaluation/README.md` documents every result
directory. All prompts and responses are in English; the domain is Linux
per-thread timing configuration on one host. No demographic information is
involved.

**B6. Did you report relevant statistics like the number of examples, details
of train/test/dev splits, etc.?**
Yes. §4: 200 runs and 8,000 events split by wake-up period into training
(2 ms), retrieval (3 ms), calibration (4 ms) and test (5 and 8 ms), ten blocks
per period, 40 events per run; 250 LLM calls (249 valid); 97 audited claims
(28 local, 69 hosted); 50 full-context answers with 285 citations (§5.2).

---

## C. Did you run computational experiments?

Yes.

**C1. Did you report the number of parameters in the models used, the total
computational budget (e.g., GPU hours), and computing infrastructure used?**
Yes. Parameter scale is given by the model names (7B–550B); Appendix C
(Compute budget) reports the infrastructure and budget:
- Local models: 4-bit GGUF (Q4_K_M; Phi-4 Q4_K) with llama-cpp-python 0.3.35
  on a four-core CPU container, no GPU, `n_ctx`=8192. Total wall time
  11,580 s (about 3.2 CPU-hours): Qwen2.5-7B 1,603 s, Llama-3.1-8B 2,325 s,
  Qwen2.5-14B 3,136 s, Phi-4 4,516 s.
- Hosted models via OpenRouter: 1,224 s total wall time over 150 calls; total
  cost about 0.5 USD.
- Kernel measurements: one Intel Core i5-3570 host (four logical CPUs,
  Linux 6.17.0-23-generic); acquisition took 6.54 s (training), 8.29 s
  (retrieval) and 10.15 s (calibration), plus the test grid.
- Optimizer baselines: replay over 1,000 seeds on the same CPU (seconds).

**C2. Did you discuss the experimental setup, including hyperparameter search
and best-found hyperparameter values?**
Yes. §4 and Appendix C: temperature 0 (greedy), five seeds (4088–4092), one
system prompt, JSON schema (config enum, at most six citations restricted to
supplied IDs, explanation of at most 400 characters), local `max_tokens` 384,
hosted `max_tokens` 4096. No prompt or hyperparameter search was performed;
the prompt was fixed before the runs. Optimizer settings (ε = 0.1, budgets
4/8/16/40, GP-EI) are in Appendix B.

**C3. Did you report descriptive statistics about your results (e.g., error
bars around results, summary statistics from sets of experiments), and is it
transparent whether you are reporting the max, mean, etc. or just a single
run?**
Yes. Held-out outcomes are means of ten block-level P95 values with 95%
Student-t half-widths (Table 2, §5.1); every claim, citation and decision
count is reported with its denominator. The paper states that greedy local
runs were byte-identical across seeds, so seeds are not independent
replicates (§4, Limitations).

**C4. If you used existing packages (e.g., for preprocessing, normalization,
or evaluation), did you report the implementation, model, and parameter
settings used?**
Yes. llama-cpp-python 0.3.35 with JSON-schema grammar (§4, Appendix C);
OpenRouter with strict `json_schema` response format restricted to providers
that honor it; NumPy/SciPy/Matplotlib for analysis
(`code/evaluation/requirements.txt`). Every model file's SHA-256 is recorded
in the released `plan.json` files.

---

## D. Did you use human annotators (e.g., crowdworkers) or research with human participants?

Yes. One author verified the 97 AI-drafted explanation-claim labels, and one
further annotator who is not an author labeled all claims blind for an
agreement study (Cohen's kappa 0.918). No crowdworkers were involved.

**D1.** Yes. The labeling rules are in §4; the second annotator received the
written guidelines (`paper/second-annotator-guidelines.md`, label definitions,
rules and the evidence values) and the blind sheet.

**D2.** Yes. The second annotator is a fellow researcher who volunteered to
contribute to the research without payment; no one was recruited through a
platform or paid.

**D3.** Yes. The second annotator consented to labeling and to the public
release of their labels and the aggregate agreement (in anonymized form). No
data from people are used.

**D4.** N/A. Labeling numeric claims about machine measurements is not
human-subjects research; no personal data were collected.

**D5.** N/A beyond "one author and one non-author annotator"; the labels are
factual checks of numbers against a table.

---

## E. Did you use AI assistants (e.g., ChatGPT, Copilot) in your research, coding, or writing?

Yes.

**E1. Did you include information about your use of AI assistants?**
Yes. The Ethics Statement states that the research idea, problem formulation
and study design are the authors'; that AI assistants were used for code, for
drafting and restructuring prose, for locating references and for drafting the
explanation-claim labels; that every reference was checked against its
publisher, ACL Anthology, Crossref or arXiv record (all 65 entries, checked
2026-10-01); and that every claim label is released with its check.

---

## Pre-submission to-do (from the answers above)

1. Done (2026-10-05): one author verified all 97 claim labels with no changes;
   `claim-audit.json`, §4, Limitations, Ethics and Appendix C are updated.
2. Upload the anonymized zip as supplementary material (software and data):
   `python3 scripts/make_anonymous_release.py --out <dir> --zip`, run on the
   final commit; see `paper/anonymous-review.md`.
3. Done: the paper now calls the system GroundKern and the anonymized release
   renames it, so searching the paper's system name no longer leads to the
   public repository. Making the repository private during review would remove
   the remaining, small risk that reviewers find it through other wording.
4. Fill in the ARR form from `paper/arr-submission-form.md`.

## Final format check (2026-10-05)

- Official ACL style files, unmodified (`acl.sty`, `acl_natbib.bst` identical
  to acl-org/acl-style-files); review mode with line numbers; A4.
- Body ends on page 8; unnumbered Limitations (required) and Ethics Statement
  on page 9; references and appendix follow.
- Abstract 200 words (ACL limit: no more than 200).
- No undefined references or citations, no overfull boxes; all fonts
  embedded, no Type 3 fonts; PDF metadata carries no author.
- Anonymity: no author name, e-mail, earlier venue, old project name, self-
  citation or acknowledgments in the PDF text; system named GroundKern.
- aclpubcheck (final-mode build): "All Clear!".

