#!/usr/bin/env bash
set -euo pipefail

# Runs 6 workloads described in the paper's Evaluation setup:
# (1) web, (2) oltp (TPC-C-like), (3) streaming (Kafka/Spark-like),
# (4) sensor (IoT), (5) hpc_ml (GPU inference-like), (6) audio (real-time audio).
# For reproducibility, this mock script just calls the telemetry agent endpoint
# to generate snapshots and trigger recommend/apply cycles.
#
# Usage:
#   ./workloads/run_workload.sh         # run all sequentially
#   ./workloads/run_workload.sh web     # run a single workload

TEL_URL="${TEL_URL:-http://localhost:7000/simulate_once}"

workload="${1:-ALL}"

run_one() {
  local w="$1"
  echo "▶ Running workload: $w"
  # 5 iterations per workload for the demo
  for i in $(seq 1 5); do
    curl -s -X POST "$TEL_URL?workload=$w" -H 'Content-Type: application/json' -d '{}' >/dev/null || true
    sleep 0.5
  done
  echo "✓ Completed: $w"
}

if [[ "$workload" == "ALL" ]]; then
  for w in web oltp streaming sensor hpc_ml audio; do
    run_one "$w"
  done
else
  run_one "$workload"
fi

echo "All requested workloads finished."
