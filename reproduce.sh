#!/usr/bin/env bash
# Reproduce every SemantOS paper table/figure offline (no Docker required).
set -euo pipefail
cd "$(dirname "$0")"

PY=${PYTHON:-python3}
echo ">> installing reproduce deps (numpy/scipy/matplotlib) ..."
$PY -m pip install -q -r reproduce/requirements.txt || true

echo ">> running reproduction harness ..."
$PY -m reproduce.run_all

echo ">> rendering figures ..."
$PY -m reproduce.figures

echo
echo ">> artifacts in reproduce/results/:"
ls -1 reproduce/results/
