# Provenance-first evaluation

The evaluation pipeline accepts **only independently collected run-level CSV**.
There is no response simulator, paper-target constant, or noise generator in this
repository. Copy `raw_runs.schema.csv`, add one row per completed hardware run,
and preserve the original log outside this repository. `raw_log_sha256` binds a
row to that immutable source log.

Required lineage:

```
hardware runner -> immutable raw log -> run-level CSV -> run_all.py -> summary.json
```

Run from `code/`:

```bash
python -m reproduce.run_all /path/to/raw_runs.csv --output reproduce/results/summary.json
python -m unittest reproduce.test_run_all
```

The validator rejects missing fields, duplicate run IDs, invalid data splits,
and impossible anomaly counts. Only `split=test` contributes to summaries.
Workload families used for test must be excluded from graph induction, retrieval,
training, validation, and calibration before a result is publishable. The
summary records the input SHA-256 and derives anomaly rate as
`anomaly_count / window_count`; a precomputed anomaly percentage is never
accepted as evidence.

No empirical result CSV is checked in. Results must be regenerated from the raw
logs supplied by the experiment owner.
