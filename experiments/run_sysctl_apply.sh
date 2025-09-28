#!/usr/bin/env bash
set -euo pipefail
# Requires root. Example:
#   sudo -E bash experiments/run_sysctl_apply.sh
python -m semantos.cli --applier sysctl --seed 42 --trials 12 --apply
