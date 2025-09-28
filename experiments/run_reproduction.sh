#!/usr/bin/env bash
set -euo pipefail
python -m semantos.cli --seed 42 --trials 16
echo "Sandbox sysctl:"
echo "---------------"
cat experiments/sandbox/sysctl.conf || true
echo
echo "Results:"
echo "--------"
cat experiments/results/summary.csv
