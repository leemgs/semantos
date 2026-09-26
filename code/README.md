# SemantOS prototype and measurement tools

**Runtime scope: dry run.** `/apply` validates and gates one complete bundle,
returns `applied: []`, and reports simulated members separately. Staging and
cancellation affect process memory only. The console must not be read as evidence
that kernel settings changed. VM-sysctl actuation and traffic isolation remain absent.
The separate `evaluation/controlled_kernel.py` adapter applies and restores only
timer slack and affinity in fresh owned child threads; it is not a REST deployment actuator.

## Measurement and verification

```bash
cd code
python3 evaluation/measure_local.py --out evaluation/results/new-run --runs 10 --operations 100
python3 evaluation/analyze.py evaluation/results/new-run
python3 -m unittest discover -s tests -v
```

See [evaluation/README.md](evaluation/README.md) for prerequisites, formats,
metrics, leakage checks, graph induction and the controlled experiment protocol.
These tools consume measured outcomes, never manuscript targets. The checked-in
local baseline has no interventions and does not prove SemantOS improves latency.

## Prototype services

From this directory, `docker compose up -d --build` starts the demo where Docker
is available. Host ports: telemetry 9101, KB 9102, reasoner 9103, runtime 9104,
console 9988. Internal services listen on 8000 (console 9988).

- Telemetry's legacy eBPF buckets are explicitly marked demonstration proxies,
  not end-to-end latency; they cannot substantiate SLO claims.
- KB seeds are empty until validated measurements are supplied. Existing Neo4j
  volumes may still contain historical edges: use a fresh experiment namespace
  and a frozen evidence manifest. Never silently mix historical seed data.
- Configure `OLLAMA_MODEL` explicitly for an installed model and retain its digest;
  the previous Llama 3.1 13B default did not exist. No trained checkpoint is supplied.
- The reasoner abstains without usable measured telemetry or a configured model.
  Its agreement/edge-weight score is heuristic, not a calibrated probability.
- Runtime calibration starts at tau=0 (veto all); calibration records require
  finite scores and boolean labels. Calibration diagnostics are in-sample and do
  not prove a guarantee under drift or selective labeling.
- The example policy permits only three documented VM controls. Joint dirty-ratio
  edits supply both values and use one bundle ID. Kernel availability must be
  inventoried on the actual execution host before real actuation is implemented.

`make reproduce RAW_RUNS=/path/to/raw_runs.csv` preserves the upstream raw-run
validator. It consumes supplied measurements and does not synthesize results.
Its `--raw-log-dir` option verifies content-addressed raw bytes against the CSV's
digests. Without that option, digest syntax alone is checked. Results remain
separate by workload, server and kernel; pooled anomaly CIs are not manufactured.
`make figures`, `make data`, and `make kb-seed` fail deliberately:
the former workflow generated table-matching synthetic values, not measurements.
Unchanged historical material is retained under [legacy/](legacy/).
