#!/usr/bin/env python3
"""
kb/induce_edges.py — offline induction of the typed dependency graph.

Runs the pairwise co-tuning sweep (reproduce/depgraph.py) that estimates each
knob-pair interaction as the deviation of the joint effect from the additive
single-knob effects, then emits kb/seed_edges.json in the schema kb-service's
`/kb/induce_from_seed` expects:

    [{ "from", "to", "edge_type", "sign", "weight", "evidence" }, ...]

edge_type in {synergizes_with, conflicts_with, depends_on}; sign is +1 for a
reinforcing coupling and -1 for an opposing one; weight in [0,1] is the
(bootstrap-significant) interaction magnitude.

Usage:
    python kb/induce_edges.py --out kb/seed_edges.json --seed 0
"""
import argparse
import json
import os
import sys

# make the reproduce package importable whether run from repo root or kb/
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from reproduce.depgraph import induce_edges  # noqa: E402

# map internal hyphenated types to the KB's underscore vocabulary + a sign
_TYPE_MAP = {
    "synergizes-with": ("synergizes_with", +1),
    "conflicts-with": ("conflicts_with", -1),
    "depends-on": ("depends_on", +1),
}


def build(seed: int, n_boot: int, alpha: float):
    edges = induce_edges(seed=seed, n_boot=n_boot, alpha=alpha)
    out = []
    for e in edges:
        etype, sign = _TYPE_MAP.get(e.etype, (e.etype.replace("-", "_"), 1))
        out.append({
            "from": e.src,
            "to": e.dst,
            "edge_type": etype,
            "sign": sign,
            "weight": round(float(e.weight), 4),
            "evidence": max(1, int(round(n_boot / 20))),
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "kb", "seed_edges.json"))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n-boot", type=int, default=200)
    ap.add_argument("--alpha", type=float, default=0.05)
    args = ap.parse_args()

    edges = build(args.seed, args.n_boot, args.alpha)
    with open(args.out, "w") as f:
        json.dump(edges, f, indent=2)
    print(f"induced {len(edges)} typed edges -> {args.out}")
    by_type = {}
    for e in edges:
        by_type[e["edge_type"]] = by_type.get(e["edge_type"], 0) + 1
    for t, c in sorted(by_type.items()):
        print(f"  {t:16s} {c}")


if __name__ == "__main__":
    main()
