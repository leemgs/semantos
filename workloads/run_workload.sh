#!/usr/bin/env bash
set -euo pipefail

# Run all six workloads described in the paper's Evaluation setup.
# Workloads: web, oltp, streaming, sensor, hpc_ml, audio
#
# Usage:
#   ./workloads/run_workload.sh             # runs all workloads sequentially
#   ./workloads/run_workload.sh web audio   # runs only specified workloads
#
# Each workload writes logs into ./outputs/<workload>/ with a simple, reproducible simulator.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${ROOT_DIR}/outputs"
mkdir -p "${OUT_DIR}"

WORKLOADS=("web" "oltp" "streaming" "sensor" "hpc_ml" "audio")

if [[ $# -gt 0 ]]; then
  WORKLOADS=("$@")
fi

run_one() {
  local name="$1"
  local dir="${OUT_DIR}/${name}"
  mkdir -p "${dir}"
  local ts="$(date -u +"%Y%m%dT%H%M%SZ")"
  local log="${dir}/run_${ts}.log"
  echo "▶ Running workload: ${name}"
  echo "timestamp,metric,median_ms,p95_ms,throughput,anomaly_rate" > "${log}"

  # Simple deterministic simulator for reproducibility – replace with real drivers later.
  # We randomize slightly using a fixed seed-like sequence.
  for i in $(seq 1 10); do
    case "${name}" in
      web)
        median=$(( 18 + i % 4 ))
        p95=$(( median + 9 + (i % 3) ))
        thpt=$(( 1000 + 25 * i ))
        anom=$(( 20 + (i % 3) ))
        ;;
      oltp)
        median=$(( 22 + (i % 5) ))
        p95=$(( median + 11 + (i % 4) ))
        thpt=$(( 800 + 30 * i ))
        anom=$(( 30 + (i % 4) ))
        ;;
      streaming)
        median=$(( 20 + (i % 4) ))
        p95=$(( median + 10 + (i % 2) ))
        thpt=$(( 1200 + 20 * i ))
        anom=$(( 25 + (i % 3) ))
        ;;
      sensor)
        median=$(( 17 + (i % 3) ))
        p95=$(( median + 8 + (i % 2) ))
        thpt=$(( 600 + 15 * i ))
        anom=$(( 18 + (i % 2) ))
        ;;
      hpc_ml)
        median=$(( 19 + (i % 3) ))
        p95=$(( median + 9 + (i % 3) ))
        thpt=$(( 1500 + 40 * i ))
        anom=$(( 22 + (i % 3) ))
        ;;
      audio)
        median=$(( 16 + (i % 2) ))
        p95=$(( median + 7 + (i % 2) ))
        thpt=$(( 500 + 10 * i ))
        anom=$(( 15 + (i % 2) ))
        ;;
      *)
        echo "Unknown workload: ${name}" >&2
        exit 1
        ;;
    esac
    # anomaly rate represented as basis points (0.01%) to avoid locales; convert later
    echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ"),${name},${median},${p95},${thpt},${anom}" >> "${log}"
    sleep 0.1
  done
  echo "✓ Done: ${name}. Log -> ${log}"
}

for w in "${WORKLOADS[@]}"; do
  run_one "${w}"
done

echo "All selected workloads completed. Outputs in ${OUT_DIR}"
