#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
: "${RAW_RUNS:?set RAW_RUNS to an independently collected run-level CSV}"
${PYTHON:-python3} -m reproduce.run_all "$RAW_RUNS" --output reproduce/results/summary.json
${PYTHON:-python3} -m unittest reproduce.test_run_all
