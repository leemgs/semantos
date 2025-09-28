#!/usr/bin/env bash
set -euo pipefail
python -m semantos.cli --applier sysctl --seed 42 --trials 12
