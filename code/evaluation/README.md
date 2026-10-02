# Measurement and evaluation tools

The tools here never import manuscript targets or `legacy/`. The checked-in
`results/local-2026-09-26/` contains **measured local baselines**, not tuning gains.
All writes by the local measurement runner are confined to its output directory.

## Prospective controlled follow-up

```bash
python -B evaluation/controlled_kernel.py --out evaluation/results/new-controlled-run
python -B evaluation/analyze_controlled.py evaluation/results/new-controlled-run
```

The output directory must be new. This bounded Linux experiment changes only the
calling thread in fresh children, snapshots both settings, checks applied values,
and restores/readbacks both original values in a `finally` path. It does not write
host sysctls, change the parent, or create production traffic canaries. Timerslack
and affinity are sequential writes, not atomic kernel state.

The checked-in [follow-up](results/controlled-2026-09-26/summary.md) has 280 child
executions: 200 fixed-window measurements (8,000 events) and 80 staged runs (1,696
events). Train/retrieval/calibration/test periods are 2/3/4/{5,8} ms, with ten
blocks of all four configurations each. This is a declared period-level split
within one workload family/host, not evidence of hardware or family generalization.
The plan precedes acquisition, score and selector freeze precedes calibration,
and gate freeze precedes test; the analyzer validates their timestamps and source
lineage. SHA-256 is an integrity check, not independent authentication of execution.

The empirical minimum and saturated two-factor representation use exactly the
same four training means and both select control. Their paired replay improvement
is zero. This is a no-LLM comparison on shared test outcomes, not BO/RL, a fresh
live-controller experiment or LLM ablation. Graph induction emitted no significant
interaction edge. Offline training/retrieval/calibration costs are retained.

A candidate run is unsafe when >10% of its 40 events exceed 200us lateness. A
configuration's training miss fraction is the frozen score; it is not the REST
model score. Held-out gate replay supplies all confusion counts and denominators,
including 5/25 and 4/24 unsafe misses. Three predeclared alpha values give the same
threshold due to ties. No exchangeability, nominal empirical coverage, drift
recovery, or production-harm reduction is inferred.

Separate staged executions observe 8/16/32 events, stop on a >10% miss fraction,
and restore both original settings. Of 80 runs, 66 stop and 14 complete; all 80
restore. Stage-trigger labels are not independent rollback ground truth. The
analyzer deliberately reports rollback precision as null. The sample count
depends on early stopping, so raw fractions cannot measure causal safety benefit.

## Matched-budget BO and RL baselines

```bash
python3 evaluation/optimizer_baselines.py evaluation/results/controlled-2026-09-26 \
  --out evaluation/results/new-optimizer-baselines --tex ../paper/optimizer-baselines.tex
```

Random search, epsilon-greedy Q-learning (epsilon 0.1), UCB1 and GP expected
improvement (fixed RBF kernel on log10 slack and all-CPU indicator, standardized
log P95) each evaluate B in {4, 8, 16, 40} training-period runs, after one
evaluation per configuration. An evaluation returns the P95 of one recorded 2 ms
training run of the chosen configuration, drawn with replacement; B=40 matches the
table selector's forty runs. The recommendation (lowest observed or posterior mean)
is scored by the same paired held-out replay as the other selectors, over 1,000
string-seeded replicates, and test outcomes are read only afterwards.

[Recorded result](results/optimizer-baselines-2026-09-27/summary.md): all methods
converge on control (98-99% at B=40, expected paired change -1 to -3%); with B=4
only 62-65% choose it (-51 to -55% at 5 ms), because single-CPU training runs are
noisy. Mean evaluations of the 1 ms settings at B=40: GP-EI 2.5, epsilon-greedy 3.8,
UCB1 12.0, random 19.8. Control is best at both test periods, so this task cannot
show a gain for any selector. This is offline replay of measured runs, not new
closed-loop acquisition.

## Executable model and context audit

```bash
python -B evaluation/model_audit.py evaluation/results/controlled-2026-09-26 \
  --out evaluation/results/new-model-audit --model INSTALLED_MODEL \
  --manifest /path/to/its/ollama/manifest
```

The command records model manifest, exact system/input prompts, fixed seeds,
decoding limits, raw responses, citation validation and elapsed time. It never
sends calibration or test outcomes to the model. Five seeds compare full, no-graph,
no-retrieval and model-only context. Cited-context deletion is compared with the
same number and kind of uncited items; missing controls are non-estimable. A valid
response alone is not an effect estimate. This frozen-input audit is retrospective
and specific to the four measured per-thread configurations, not a VM-sysctl run.

The first [recorded attempt](results/model-audit-2026-09-26/status.json) produced
zero responses: the local socket was forbidden. Its failure is not a measured zero
effect. Completed Qwen2.5-7B and Llama-3.1-8B runs are summarized under
"Running the LLM audit" below. The installed Llama 3.2 manifest does not replace historical Llama 3.1
provenance. Tests use explicit fixtures for failure/citation handling and never
count fixture output as model evidence.

## Run and analyze actual local work

From `code/`, with Python 3.10+ and `evaluation/requirements.txt` installed:

```bash
python3 evaluation/inventory.py
python3 evaluation/measure_local.py --out evaluation/results/new-run --runs 10 --operations 100
python3 evaluation/analyze.py evaluation/results/new-run
```

The output directory must be new. Three microbenchmarks execute real operations:
SQLite WAL/FULL commits of 4 KiB values, overwriting/fsync of a 64 KiB file, and
zlib compression/decompression verification of a seeded 64 KiB buffer. There are
10 warm-ups per invocation and shuffled workload/run order (seed 4088). No kernel
knob changes, root access, model inference, or global package installation occurs.
Every operation records monotonic elapsed time, an error indicator and a fixed
50 ms deadline. An anomaly means error OR deadline exceedance, divided by **all
measured operations**. It is independent of the runtime's veto/rollback actions.

The analyzer verifies the raw SHA-256, reports per-run median and P95, and computes
Student-t intervals over run summaries. It does not pool different workloads or
claim a zero population risk from zero observed events. Limitations: single shared
host, serial closed-loop load, no CPU isolation/cache drop, short duration, possible
run dependence. These tasks are not TPC-C, Kafka/Spark, web, audio or GPU workloads.

## Controlled tuning experiment (requires an isolated writable test host)

1. Freeze workload versions, exact commands, offered load, warm-up and measurement
   durations, request deadlines, allowed knob grid, objective weights, reset policy,
   paired seeds, trial/time budgets and failure-stop policy before running methods.
2. Record CPU/memory/storage, kernel build/config, governor, affinity/NUMA, container
   limits, sysctl snapshot, software versions, model ID and digest, decoding settings,
   actual prompts, graph/retrieval/calibration hashes, and execution timestamps.
3. Partition workload/hardware/acquisition-session groups **before** constructing any
   graph or other artifact. Use disjoint train/retrieval/calibration/test groups.
4. Measure unchanged kernel and expert profiles, cold conventional optimization,
   graph-aware conventional optimization with the same evidence, deterministic
   graph policy, full SemantOS, and no-graph/no-RAG/no-LLM variants. Charge the same
   online budgets and separately report all offline costs. No-safety trials require
   an isolated host; they must never be run on production traffic.
5. A real actuator must be implemented and tested before this comparison: snapshot,
   joint validation, serialized writes, readback, full restoration on partial failure,
   missing/stale telemetry stop, and multi-host or equivalent traffic isolation.
   The current runtime has no such actuator. Multiple host sysctls are not an atomic
   transaction and cannot provide a per-request traffic canary on one shared host.
6. Retain one raw record per request and one decision record per bundle. Measure
   rollback exposure and action labels independently. Unknown counterfactual labels
   for rejected proposals remain null; do not infer safety from rejection.
7. Report absolute metrics by workload and hardware, paired baseline-relative ratios,
   and uncertainty over independent runs. Sweep objective weights or common budgets
   to obtain multiple points per method before drawing a nondominated frontier.
8. Drift runs evaluate each frozen gate on subsequent independent data, logging
   alpha, unsafe calibration count, window size, thresholds and change schedule.
   There is no automatic recovery theorem from a sliding window.
9. Faithfulness: remove cited context and matched uncited controls under fixed model
   seeds; retain prompts, proposed bundles and attribution/decision differences.
   Explanation preference is a different outcome. No human study is needed for this.

These are experiment requirements, not claims that the original six workload
adapters, optimizers or deployment machinery have already been implemented.

## Executable data checks

`validate_split.py manifest.json` requires:

```json
{
  "records": [{"id": "source-1", "group": "workload-hardware-session",
               "role": "train", "sha256": "64 lowercase hex characters"}],
  "artifacts": [{"kind": "graph", "sources": ["source-1"]}]
}
```

Roles: train/retrieval/calibration/test. Model and graph lineage may use train;
retrieval_index uses retrieval; calibrator uses calibration; evaluation uses test.
The validator rejects duplicate IDs, overlapping groups, cross-role identical
hashes and missing/forbidden sources. It validates declarations, not the truth of
acquisition; raw logs and the frozen pipeline remain necessary.

`induce_graph.py sweeps.jsonl --out graph.json` consumes one independently measured
four-configuration block per run:

```json
{"id":"sweep-1","split":"train","source":"measured","group":"scope-id",
 "pair":["vm.dirty_background_ratio","vm.dirty_ratio"],"run":0,
 "losses":{"baseline":100,"a":90,"b":90,"joint":70}}
```

The values above illustrate the schema, **not a result**. Supply at least 10 runs
per scoped pair. It bootstraps normalized joint-minus-additive contrasts, emits
only intervals excluding zero, and retains source IDs. Multiplicity adjustment
and a held-out confirmation are still needed for a large pair search. It cannot
infer `depends_on` from a contrast alone. The output is a versioned artifact, not
a command that automatically populates a live KB.

`safety_counts.py decisions.jsonl` consumes one record per unique bundle:

```json
{"bundle_id":"b1","decision":"accepted","unsafe":null,"rolled_back":false}
```

Allowed decisions: accepted/vetoed/invalid. An independently assessed label is
true or false; an unobserved outcome is null. Reports gate confusion counts,
unsafe-given-accepted, acceptance-given-unsafe, veto-given-safe, and separate
rollback precision with an explicit labeled-only denominator. Missing labels
may bias all conditional metrics; the tool makes no recovery or efficacy claim.

## Tests and packaging

```bash
python3 -m pip install -r tests/requirements.txt
make test
python3 evaluation/package_revision.py --out /tmp/semantos-revision.zip
```

Regression-test fixtures are synthetic by design and test mathematics/data handling;
they are not used in the measured result table. Packaging excludes legacy
artifacts, Git history, caches, credentials and unapproved live output directories.
Check the ZIP against the target venue's anonymity rules before uploading it.

## Executed per-process kernel intervention experiment

`measure_kernel_local.py` runs fresh owned children, sets and reads back Linux
`PR_SET_TIMERSLACK` and CPU affinity, then measures periodic wake-up lateness.
It needs no host sysctl writes or network service. It leaves parent settings
unchanged. Python overhead and uncontrolled shared-host load remain part of the
measurement. This driver is independent of the SemantOS dry-run actuator.

```sh
python code/evaluation/measure_kernel_local.py --out /tmp/new-kernel-measurement
python code/evaluation/analyze_kernel_local.py /tmp/new-kernel-measurement
```

The output path must be new. The plan precedes execution. Five randomized
training blocks select minimum mean run P95 at each period; selection is saved
before ten test blocks. Four configurations combine 50,000/1,000,000 ns timer
slack with all available CPUs/first CPU affinity. Each case has 10 warm-up and
80 recorded absolute-target wake-ups at 2 or 5 ms. A miss is lateness >200 us.
The control explicitly sets 50,000 ns slack and all available CPUs. No energy
outcome is recorded. Test counts are 800 events per interval/configuration;
training plus test totals 9,600 events in 120 child invocations. P95 uses the
nearest-rank definition. Student-t intervals use ten run/block units, not events.
Paired differences compare configurations within block, not simultaneous runs.
The temporal split does not demonstrate generalization to held-out workloads.

Read [the measured summary](results/kernel-local-2026-09-26/summary.md).
The selected policy equals control at both periods: measured selected-policy
gain is zero. Other configurations are sensitivity interventions, not proposed
SemantOS recommendations. No LLM or graph optimizer result follows from this.

Interface definitions: [Linux timer slack](https://man7.org/linux/man-pages/man2/PR_SET_TIMERSLACK.2const.html)
and [CPU affinity](https://man7.org/linux/man-pages/man2/sched_setaffinity.2.html).

## Paper figure

`plot_gate_replay.py --out <pdf>` draws the frozen-gate replay (paper Figure 2)
from `results/controlled-2026-09-26/`. It first runs the same hash, lineage and
freeze checks as `analyze_controlled.py`, and refuses to plot if its recomputed
FN/TP counts differ from `analysis.json`.

## Running the LLM audit (paper: "Model and explanation audit")

`model_audit.py` gives a model exactly the frozen training table, interaction
graph and retrieval runs, never test outcomes. For each of five seeds it runs
full / no-graph / no-retrieval / model-only prompts plus cited vs. matched
uncited context deletion, validates every citation, and then scores each valid
choice on the held-out grid with the same paired-replay rule used for the
non-LLM selectors (`heldout.json`). Decoding is constrained by a JSON-schema
grammar: `config` must be an allowed name and citations must be supplied IDs.

```
pip install -r evaluation/requirements-llm.txt   # builds llama.cpp from source if no wheel
# the official Qwen GGUF is published as two shards; pass the first
huggingface-cli download Qwen/Qwen2.5-7B-Instruct-GGUF \
    --include 'qwen2.5-7b-instruct-q4_k_m-0000?-of-00002.gguf' --local-dir models/
huggingface-cli download bartowski/Meta-Llama-3.1-8B-Instruct-GGUF \
    Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf --local-dir models/
python3 evaluation/model_audit.py evaluation/results/controlled-2026-09-26 \
    --backend llamacpp --gguf models/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf \
    --model Qwen2.5-7B-Instruct-Q4_K_M \
    --out evaluation/results/model-audit-qwen2.5-7b
# exploratory, post hoc: partially matched cited-deletion probe (one seed)
python3 evaluation/cited_deletion_probe.py evaluation/results/controlled-2026-09-26 \
    evaluation/results/model-audit-qwen2.5-7b --gguf models/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf \
    --out evaluation/results/model-audit-qwen2.5-7b/probe-cited-deletion
python3 evaluation/summarize_model_audit.py evaluation/results/model-audit-qwen2.5-7b \
    evaluation/results/model-audit-llama3.1-8b --out evaluation/results/model-audit-summary \
    --tex ../paper/model-audit.tex
```

The run records the SHA-256 of every GGUF shard and its `general.*` metadata in
`plan.json`. A 7B Q4 model needs about 6 GB RAM. `--backend ollama --manifest
<file>` targets a local Ollama server instead. Use `--purpose pipeline-check` for
plumbing tests with toy models; such runs must not be reported as results, and the
summarizer refuses them.

### Hosted models through free APIs (`--backend api`)

Larger models than a four-core CPU can hold are run through OpenAI-compatible APIs.
Keys are read only from `OPENROUTER_API_KEY`, `GEMINI_API_KEY` or `CHATGPT_API_KEY`
and are never written to results. Prompts, evidence, seeds, the answer schema and
held-out scoring are identical to local runs.

```
python3 evaluation/model_audit.py evaluation/results/controlled-2026-09-26 \
    --backend api --provider openrouter --model nvidia/nemotron-3-super-120b-a12b:free \
    --response-format json_schema --out evaluation/results/model-audit-api-nemotron-super
python3 evaluation/cited_deletion_probe.py evaluation/results/controlled-2026-09-26 \
    evaluation/results/model-audit-api-nemotron-super \
    --out evaluation/results/model-audit-api-nemotron-super/probe-cited-deletion
```

`--response-format json_schema` sends the local grammar's schema (OpenRouter is
told to route only to providers that honor it); `json_object` or `none` fall back
to the prompt and still re-validate every answer. A single surrounding Markdown
fence is removed and flagged. Each call records the provider-reported model,
response id, fingerprint, routing and any retried 429/5xx errors. Hosted weights
cannot be hashed and may change or be re-routed, so API results are reported as
less reproducible than the local GGUF runs. `--min-interval` (default 6 s) paces
requests for free-tier rate limits.

The local runs above used `model_audit.py` as of commit 437076c (the hash in
their `plan.json`); adding the API backend did not change the local code path.

### Recorded results (2026-09-26)

[`results/model-audit-summary/summary.md`](results/model-audit-summary/summary.md)
summarizes four runs, all on a four-core CPU container with llama-cpp-python
0.3.35 and weights whose SHA-256 equal the publishers' Hugging Face LFS hashes:

| Model | Weights SHA-256 | Calls | Mean s/call |
|---|---|---|---|
| Qwen2.5-7B-Instruct Q4_K_M (2 shards) | `dfce12e3…` + `539cf93f…` | 20/20 valid | 80.2 |
| Llama-3.1-8B-Instruct Q4_K_M | `7b064f58…` | 30/30 valid | 77.5 |
| Qwen2.5-14B-Instruct Q4_K_M (3 shards) | `a09ea5e7…` + `21b9457d…` + `c8d37006…` | 20/20 valid | 156.8 |
| Phi-4 Q4_K (microsoft/phi-4-gguf) | `5652b9be…` | 30/30 valid | 150.5 |

* Responses were byte-identical across the five seeds (greedy decoding), so the
  seeds are not independent replicates.
* Qwen chose the explicit control in the full, no-graph and no-retrieval contexts
  (paired improvement exactly zero, as for the non-LLM selectors) and 50 us slack
  on one CPU without evidence (-145 +- 125 % and -180 +- 156 % at 5/8 ms).
* Llama chose 50 us slack on one CPU in all four contexts, i.e. worse than control
  on replay even when given only the training table.
* Qwen2.5-14B behaves like Qwen2.5-7B. Phi-4 chooses control with evidence and
  1 ms slack on one CPU without it (-631 +- 183 % and -699 +- 206 %).
* Phi-4 is the only model with an estimable, citation-specific preregistered
  result: deleting its six cited runs changes the action for all seeds, deleting
  six matched uncited runs for none. Its preregistered controls are runs of other
  configurations; the post hoc probe, whose controls are other runs of the chosen
  configuration, agrees. The changed choices are not evidence-driven, because the
  remaining runs still favor control.
* Faithfulness: Qwen cites the single training table, which has no same-kind
  control, so it is non-estimable. For Llama, deleting cited and matched uncited
  runs both changed the action, so its sensitivity is not citation-specific.
  The post hoc probe (`probe-cited-deletion/`) found citation-specific sensitivity
  for Qwen in one deterministic response; this is not a faithfulness estimate.
* [`claim-audit.json`](results/model-audit-summary/claim-audit.json) checks all 28
  quantitative claims in the 20 distinct explanations (labels drafted with an AI
  assistant and released with their checks; see `claim_review_agreement.py`): 7 correct, 1 partly
  wrong, 4 unsupported priors, 16 wrong, misattributed, overstated or in the wrong
  unit (8 of 12 for the 7-8B models, 8 of 16 for the 14B models). All quoted
  decimals occur in the prompt, so citation checks verify provenance, not
  correctness.
* [`claim_taxonomy.py`](claim_taxonomy.py) tabulates every labeled claim (local
  and hosted) by model and error type and writes the paper's claim table
  (`python3 claim_taxonomy.py --out ../../paper/claim-taxonomy.tex`).
* [`claim_label_autocheck.py`](claim_label_autocheck.py) re-derives the expected
  label of claims whose form a rule can decide (56 of 97: values attributed to
  the training table, run lists, superlatives, ranges, thresholds, units,
  no-evidence claims) from the evidence; all drafted labels agree, and a
  mutation test (`--mutation-test`) detects 76 of 97 flipped labels. With
  `--csv` it adds an `auto_check` column to the review sheet.
* [`claim_review_agreement.py`](claim_review_agreement.py) exports the drafted
  claim labels for human review (`paper/claim-label-review.csv`), reports
  agreement and Cohen's kappa between the drafted and reviewed labels, and with
  `--apply` writes the verified labels back into `claim-audit.json`.
* [`citation_analysis.py`](citation_analysis.py) counts what the 50 valid
  full-context answers cite (training table, graph item, runs of the chosen or
  another configuration, and each cited run's position in the evidence list)
  and writes [`citations.json`](results/model-audit-summary/citations.json).

Hosted runs (2026-09-27, OpenRouter, `--response-format json_schema`,
`--max-tokens 4096`, `--min-interval 2`; total cost about 0.5 USD):

| Model | Valid calls | Routed providers | Mean s/call |
|---|---|---|---|
| meta-llama/llama-3.3-70b-instruct | 30/30 | AkashML, DeepInfra, Parasail | 19.8 |
| qwen/qwen3-235b-a22b-2507 | 29/30 (one truncated) | DeepInfra, GMICloud, Nebius, Novita | 8.0 |
| deepseek/deepseek-v3.2 | 20/20 | Alibaba, AtlasCloud, Baidu, DeepInfra | 5.1 |
| nvidia/nemotron-3-ultra-550b-a55b | 30/30 | DeepInfra | 2.1 |
| google/gemini-3.8-flash | 20/20 | Google AI Studio | 3.4 |
| google/gemini-3.1-pro-preview | 20/20 | Google | 7.9 |

* Unlike the local runs, hosted responses differ across seeds at temperature 0,
  and some providers ignore the schema's 400-character explanation limit.
* All six choose control whenever evidence is given. Without evidence, Llama-70B
  chooses 1 ms slack on one CPU (-631 +- 183 %, -699 +- 206 %), Qwen3-235B does so
  for 3 of 5 seeds, and DeepSeek chooses 50 us slack on one CPU. Both Gemini models choose 50 us slack on one CPU without
  evidence (-145 +- 125 %, -180 +- 156 %). Nemotron-Ultra chooses control
  without evidence too, explicitly as a "conservative" default without support.
* Faithfulness: DeepSeek and both Gemini models cite the single table (non-estimable). For Llama-70B,
  Qwen3-235B and Nemotron-Ultra neither cited nor matched uncited deletion changes the action; the
  remaining runs still favor control, so this is consistent with the evidence but
  says nothing about reliance on the cited items.
* Claim audit of the distinct full-context explanations: 44 of 69 claims correct,
  25 wrong or overstated (Llama-70B 2/7, Qwen3-235B 3/6, DeepSeek-V3.2 6/16,
  Nemotron-Ultra 10/23, Gemini Flash 2/12, Gemini Pro 2/5; every Nemotron
  explanation misstates the s50000_aone range). "Consistently lowest" is labeled
  overstated because s50000_aall is lowest in 8 of 10 retrieval blocks.
* A `nvidia/nemotron-3-super-120b-a12b` run was stopped unfinished (about six
  minutes per call); it produced no result and is not reported.

`results/model-audit-2026-09-26/` keeps the earlier failed Ollama attempt as history.
