# Reasoner training contract

The audited base checkpoint is `meta-llama/Meta-Llama-3.1-8B-Instruct`. Record
the resolved revision hash, tokenizer hash, license, trainer version, and output
checkpoint hash in every run manifest. No training corpus is fabricated or
shipped by this repository.

The experiment owner must provide context/action/outcome records and a split
manifest with four disjoint workload-family partitions: `train`, `validation`,
`calibration`, and `test`. Test-family traces and edges must not enter graph
induction, retrieval, fine-tuning, hyperparameter selection, or calibration. A
leave-one-workload-family-out run rebuilds every learned artifact from scratch.

`config.yaml` describes the intended SFT/calibration stages but contains required
input placeholders, so it cannot silently train on synthetic examples. Report
LLM-only, graph-only/rules, BO, RL, graph+LLM, and full safety-runtime baselines
with identical telemetry, search budgets, and graph access.
