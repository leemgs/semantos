# Measurement and review remediation

The tools here never import manuscript targets or `legacy/`. The checked-in
`results/local-2026-09-26/` contains **measured local baselines**, not tuning gains.
All writes by the local measurement runner are confined to its output directory.

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
they are not used in the measured result table. Packaging excludes legacy/rejected
artifacts, Git history, caches, credentials and unapproved live output directories.
The ZIP is a working artifact; conference-specific anonymity/format review is separate.

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
