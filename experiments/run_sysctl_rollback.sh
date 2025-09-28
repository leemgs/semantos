#!/usr/bin/env bash
set -euo pipefail
# Requires root. Restores previous values recorded at apply-time.
python -m semantos.cli --applier sysctl --rollback
