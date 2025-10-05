# SemantOS Reproducibility Scaffold (Mock)

This scaffold implements a **runnable demo** of the SemantOS architecture described in the paper, with the **Operator Console** at **http://localhost:9988/** and six workloads runnable via `./workloads/run_workload.sh`.

> Note: This is a mock (no privileged kernel changes). It preserves the *interfaces* (telemetry → KB → reasoner → safety → operator console) so reviewers and users can reproduce the end-to-end flow quickly.

## Quickstart

```bash
./manual.sh
# visit http://localhost:9988/
# (optional) in another terminal:
./workloads/run_workload.sh           # run all 6 workloads
./workloads/run_workload.sh web       # run a single workload
```

## Services

- **telemetry-agent** (port 7000): Emits snapshots and triggers recommend/apply cycle
- **kb-service** (port 7001): Mock knowledge base + retrieval
- **reasoner** (port 7002): Mock RAG + LLM producing TuningRecommendation (with `uncertainty_score`)
- **safety-runtime** (port 7003): Applies via staged rollout or rolls back if `u ≥ τ` (default τ=0.55)
- **operator-console** (port 9988): Web UI

## Workloads (6)

- `web`, `oltp`, `streaming`, `sensor`, `hpc_ml`, `audio` — taken from the Evaluation setup in the paper.

## Schema

See `proto/semantos.proto` (documentary; REST used in the mock).

## License

Apache-2.0 (you can change as needed).
