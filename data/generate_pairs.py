#!/usr/bin/env python3
"""
data/generate_pairs.py — build the workload x hardware pair dataset.

Produces the ~1000-example corpus the reasoner is trained on (paper Sec. 5.1):
each example is a (workload, server) context with its baseline telemetry, a
sampled candidate knob bundle drawn along the typed dependency graph, and the
realized outcome (latency/anomaly deltas, SLO-safe flag) from the calibrated
response model.  Held-out splits reserve whole workloads/servers for the
generalization study.

Output: data/pairs.jsonl  (one JSON object per line) + data/pairs_meta.json.

Usage:
    python data/generate_pairs.py --n 1000 --out data/pairs.jsonl --seed 20260705
"""
import argparse
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from reproduce import spec                      # noqa: E402
from reproduce.depgraph import DependencyGraph  # noqa: E402

# whole-entity held-out sets for the generalization study
HELDOUT_WORKLOADS = {"audio"}
HELDOUT_SERVERS = {"S3"}

_BUNDLE_SEED = "sched_min_granularity_ns"
_PROPOSALS = {
    "sched_min_granularity_ns": ["10000000", "15000000", "20000000"],
    "sched_wake_affinity": ["0", "1"],
    "sched_latency_ns": ["6000000", "12000000", "18000000"],
    "vm.dirty_ratio": ["10", "15", "20"],
    "vm.swappiness": ["10", "30", "60"],
}


def _bundle(graph, rng):
    """Sample a co-tuning bundle: seed knob + synergistic partners."""
    bundle = [_BUNDLE_SEED]
    for e in graph.synergistic_partners(_BUNDLE_SEED):
        if e.weight > 0.3 and rng.random() < e.weight:
            bundle.append(e.dst)
    # occasionally add an unrelated knob to create negative/independent examples
    if rng.random() < 0.4:
        bundle.append(rng.choice(list(_PROPOSALS.keys())))
    return list(dict.fromkeys(bundle))[:3]


def _outcome(workload, server, bundle, rng):
    """Calibrated synthetic outcome for a proposed bundle."""
    w = spec.WORKLOADS[workload]
    s = spec.SERVERS[server]
    base_p95 = w.base_p95_ms * s.latency_scale
    base_anom = w.base_anomaly_pct / 100.0
    # joint effect: strong if the synergistic pair is present, else additive-ish
    synergy = ({"sched_min_granularity_ns", "sched_wake_affinity"} <= set(bundle))
    p95_delta = -0.38 if synergy else -0.05 * len(bundle)
    p95_delta += rng.normal(0, 0.03)
    anom_delta = -0.55 if synergy else -0.15
    anom_delta += rng.normal(0, 0.05)
    new_p95 = base_p95 * (1 + p95_delta)
    new_anom = max(0.0, base_anom * (1 + anom_delta))
    slo_safe = new_p95 <= base_p95 and new_anom <= base_anom + 0.005
    return {
        "base_p95_ms": round(base_p95, 2),
        "delta_p95": round(p95_delta, 4),
        "new_p95_ms": round(new_p95, 2),
        "delta_anomaly": round(anom_delta, 4),
        "new_anomaly": round(new_anom, 4),
        "slo_safe": bool(slo_safe),
    }


def split_of(workload, server, rng):
    if workload in HELDOUT_WORKLOADS or server in HELDOUT_SERVERS:
        return "heldout"
    return "train" if rng.random() < 0.9 else "val"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--out", default=os.path.join(ROOT, "data", "pairs.jsonl"))
    ap.add_argument("--seed", type=int, default=spec.GLOBAL_SEED)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    graph = DependencyGraph.induced(seed=0)
    workloads = list(spec.WORKLOADS.keys())
    servers = list(spec.SERVERS.keys())

    counts = {"train": 0, "val": 0, "heldout": 0}
    with open(args.out, "w") as f:
        for i in range(args.n):
            wl = rng.choice(workloads)
            sv = rng.choice(servers)
            bundle = _bundle(graph, rng)
            outcome = _outcome(wl, sv, bundle, rng)
            split = split_of(wl, sv, rng)
            counts[split] += 1
            ex = {
                "id": f"pair-{i:04d}",
                "split": split,
                "context": {"workload": wl, "server": sv,
                            "base_median_ms": spec.WORKLOADS[wl].base_median_ms,
                            "base_p95_ms": outcome["base_p95_ms"],
                            "base_anomaly_pct": spec.WORKLOADS[wl].base_anomaly_pct},
                "action": {"bundle": bundle,
                           "proposals": {k: _PROPOSALS.get(k, ["auto"])[
                               rng.integers(len(_PROPOSALS.get(k, ["auto"])))]
                               for k in bundle}},
                "outcome": outcome,
            }
            f.write(json.dumps(ex) + "\n")

    meta = {"n": args.n, "seed": args.seed, "counts": counts,
            "heldout_workloads": sorted(HELDOUT_WORKLOADS),
            "heldout_servers": sorted(HELDOUT_SERVERS),
            "workloads": workloads, "servers": servers}
    with open(os.path.join(os.path.dirname(args.out), "pairs_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(f"wrote {args.n} pairs -> {args.out}")
    print(f"  splits: {counts}")


if __name__ == "__main__":
    main()
