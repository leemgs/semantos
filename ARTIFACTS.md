# Artifacts for "Cited but Not Correct"

This guide is for reviewers checking the paper and for researchers who want to
reuse the data or apply the audit protocol to their own evidence-grounded
advisor. All paths are relative to the repository root.

## 1. Reproduce every number in one command

```
pip install numpy scipy matplotlib        # Python 3.10+
python3 code/evaluation/reproduce_paper.py
```

The script copies `code/evaluation/results/` to a temporary directory, reruns
every analysis on the raw logs, and compares the regenerated LaTeX tables
byte for byte with the files the paper includes. It also recomputes the
numbers quoted in the text. Expected output: `13 of 13 checks passed`
(about 20 seconds on a laptop CPU; no GPU, no API key, no network).

## 2. Where each claim in the paper comes from

| Paper item | Data | Script |
|---|---|---|
| Table 2: LLM decisions under each input condition | `code/evaluation/results/model-audit-*/records.json` | `summarize_model_audit.py` |
| §5.1 selector and optimizer results; Appendix B tables | `results/controlled-2026-09-26/`, `results/optimizer-baselines-2026-09-27/` | `analyze_controlled.py`, `optimizer_baselines.py` |
| §5.2 citation counts (252/260, 209 in first half) | `model-audit-*/records.json` | `citation_analysis.py` → `model-audit-summary/citations.json` |
| Table 3: claim taxonomy (16/28, 25/69, 41/97) | `model-audit-summary/claim-audit.json` | `claim_taxonomy.py` |
| Table 4 and Figure 1: example misstatements | `claim-audit.json`, `model-audit-api-deepseek-v3.2/records.json` (seed 4089) | — |
| §5.4 deletion results | `model-audit-*/records.json` (`delete_cited`, `delete_uncited`) | `summarize_model_audit.py` |
| §5.5 gate replay; Appendix figure | `results/controlled-2026-09-26/` | `analyze_controlled.py`, `plot_gate_replay.py` |
| Appendix C rule check and intervals | `claim-audit.json`, prompts in `records.json` | `claim_label_autocheck.py --mutation-test` |
| §6 and Appendix C entailment-judge experiment (Table 9) | `model-audit-summary/entailment-judge.json` | `entailment_judge.py` (rerunning the judges needs `torch`, `transformers` and about 4 GB of model downloads; `--tex` rebuilds the table from the saved outputs) |
| Appendix B local and temporal-holdout measurements | `results/local-2026-09-26/`, `results/kernel-local-2026-09-26/` | `analyze.py`, `analyze_kernel_local.py` |

Each result directory contains a `plan.json` written before data collection
and, where applicable, `SHA256SUMS.json`; the analysis scripts verify these
hashes before computing anything.

## 3. Data statement

**What the data are.** (a) Timing measurements: 8,000 periodic wake-up events
from 200 runs of four per-thread Linux configurations, split by wake-up period
into training, retrieval, calibration and test roles, plus 9,600 temporal-
holdout events and 3,000 local baseline operations. (b) LLM audit records:
250 calls to ten LLMs (four local 4-bit GGUF models with recorded SHA-256
hashes, six hosted models via OpenRouter), each with the exact prompt and its
hash, the raw response, the parsed answer and, for hosted models, the routed
provider. (c) Claim annotations: 97 quantitative or comparative claims from
the explanations, each with a label and a one-line check against the evidence.

**How the claim labels were made.** Labels were drafted with an AI assistant
under fixed rules (paper §4), re-checked where possible by
`claim_label_autocheck.py` (56 of 97 claims are decided by a rule), and then
verified by one author, who changed none. This is a confirmation of the draft,
not an independent double annotation; `code/evaluation/claim_review_agreement.py`
lets a second annotator re-label the claims and reports agreement.

**Language and domain.** English prompts and responses; Linux per-thread
timing configuration on one host (Intel Core i5-3570, Linux 6.17).

**Personal data.** None: the data are machine measurements and model outputs
to a fixed technical prompt.

**Known limitations.** One task, one host and one workload family; the default
configuration is best on the test grid; hosted responses are not reproducible
bit for bit. See the paper's Limitations section.

**License.** Apache License 2.0 (`LICENSE`); stored model responses are also
subject to each model's license and provider terms (see `README.md`).

## 4. Applying the audit to your own advisor

The protocol needs four inputs, all plain JSON:

1. **Frozen evidence**: a list of items, each with a unique `id`, a `kind`
   (e.g. `table`, `retrieval`, `graph`) and its content. Include several items
   of each kind you expect models to cite, so that matched deletion has
   controls (§6, "What deletion can and cannot show").
2. **Model records**: one record per call in the format of
   `results/model-audit-*/records.json` (`variant`, `seed`, `prompt`,
   `answer` with `config`, `cited_ids`, `explanation`, and `status`).
   `model_audit.py` produces these for local GGUF models or any
   OpenAI-compatible API; its `experiment()` function builds the full,
   ablated and deleted variants from the evidence list.
3. **A non-LLM baseline** that receives the same evidence (for the decision
   level).
4. **Held-out outcomes** labeled from raw observations, never from the
   enforcement mechanism under test.

Then:

- Decision level: compare model choices with the baseline on held-out
  outcomes (`model_audit.py` `heldout()`).
- Citation level: `citation_analysis.py --results <dir>` reports the kind,
  configuration and list position of every cited item.
- Claim level: label claims with the rules in §4 (or adapt
  `claim_label_autocheck.py`'s rules to your evidence), then have a person
  verify them with `claim_review_agreement.py`.
- Reliance level: compare decisions after deleting cited versus matched
  uncited items (`delete_cited` / `delete_uncited` variants).

Extensions the paper calls for: tasks where the default is not optimal and
documentation priors could help, multi-annotator claim labels (a blind
annotation package is produced by `claim_review_agreement.py export-blind`),
and stronger attribution judges than the four off-the-shelf ones tested here
(balanced accuracy 0.51–0.68 on the 93 evidence-based claims).
