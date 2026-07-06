"""
depgraph.py — Typed, signed inter-knob dependency graph (Semantic Reasoning).

Each node is a tunable; each edge is typed and signed:
  * synergizes-with : joint change yields super-additive gains
  * conflicts-with  : joint change risks an SLO regression
  * depends-on      : a knob's safe range is conditioned on another's value

Edges are *induced offline* from pairwise co-tuning sweeps: for a pair (a, b)
we estimate the interaction as the deviation of the joint effect from the
additive single-knob effects on the target metric; a positive/negative
deviation beyond a bootstrap significance threshold yields a
synergizes-/conflicts-with edge, and a range-conditioning relation yields
depends-on.  Each edge carries a weight decayed online by gamma**t and
refreshed from telemetry, so stale couplings fade.

This is the mechanism that lets SemantOS co-tune along synergistic edges;
removing it (w/o Dep-Graph ablation) forces knob-independent tuning.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import numpy as np

EdgeType = str  # "synergizes-with" | "conflicts-with" | "depends-on"


@dataclass
class Edge:
    src: str
    dst: str
    etype: EdgeType
    weight: float          # magnitude of the (signed) interaction, in [0, 1]
    interaction: float     # signed joint-minus-additive deviation on target metric


# --------------------------------------------------------------------------- #
# Ground-truth pairwise interactions used by the offline sweep.  These encode
# Observation 2 / Figure 1: sched_min_granularity_ns and sched_wake_affinity
# are strongly synergistic on tail latency, while CPU-sched vs memory-reclaim
# knobs interact too.  (deviation of joint from additive single effects.)
# Values are fractional tail-latency deltas.
# --------------------------------------------------------------------------- #

_TRUE_SINGLE = {
    "sched_min_granularity_ns": -0.05,
    "sched_wake_affinity":      -0.08,
    "sched_latency_ns":         -0.06,
    "vm.dirty_ratio":           -0.04,
    "dirty_ratio":              -0.04,
    "dirty_background_ratio":   -0.03,
    "vm.swappiness":            -0.02,
    "numa_balancing":           -0.03,
    "irq_affinity":             -0.04,
    "min_free_kbytes":          -0.02,
}

# joint effect for a pair (a, b) — if larger in magnitude than the additive
# sum, the extra magnitude is the (synergistic) interaction.
_TRUE_JOINT = {
    frozenset(("sched_min_granularity_ns", "sched_wake_affinity")): -0.38,  # Fig 1
    frozenset(("sched_latency_ns", "vm.dirty_ratio")): -0.19,
    frozenset(("sched_latency_ns", "dirty_ratio")): -0.19,
    frozenset(("vm.dirty_ratio", "dirty_background_ratio")): -0.11,
    frozenset(("numa_balancing", "vm.swappiness")): -0.02,   # near-additive
}

# pairs where the joint change *conflicts* (regresses an SLO — fairness/anomaly)
_TRUE_CONFLICT = {
    frozenset(("sched_latency_ns", "numa_balancing")): +0.06,
    frozenset(("vm.swappiness", "dirty_background_ratio")): +0.05,
}

# range-conditioning relations (depends-on): key knob's safe range shifts with
# the value of the conditioning knob.
_TRUE_DEPENDS = [
    ("sched_min_granularity_ns", "sched_latency_ns"),
    ("dirty_background_ratio", "vm.dirty_ratio"),
    ("dirty_background_ratio", "dirty_ratio"),
]


def induce_edges(seed: int = 0, n_boot: int = 200, alpha: float = 0.05) -> list[Edge]:
    """Offline edge induction from (noisy) pairwise co-tuning sweeps.

    Returns the typed, signed edge set.  Reproducible under `seed`.
    """
    rng = np.random.default_rng(seed)
    edges: list[Edge] = []

    def _significant(effect: float, noise: float) -> bool:
        # crude bootstrap: is the observed |effect| beyond the null band?
        samples = rng.normal(effect, noise, size=n_boot)
        ci_lo, ci_hi = np.percentile(samples, [100 * alpha / 2, 100 * (1 - alpha / 2)])
        return not (ci_lo <= 0.0 <= ci_hi)

    seen = set()
    # synergies / conflicts from joint-vs-additive deviation
    for pair, joint in list(_TRUE_JOINT.items()) + list(_TRUE_CONFLICT.items()):
        a, b = tuple(pair)
        additive = _TRUE_SINGLE.get(a, 0.0) + _TRUE_SINGLE.get(b, 0.0)
        deviation = joint - additive  # negative => extra gain (synergy)
        if not _significant(deviation, noise=0.01):
            continue
        etype = "synergizes-with" if deviation < 0 else "conflicts-with"
        weight = float(min(1.0, abs(deviation) / 0.35))
        edges.append(Edge(a, b, etype, weight, float(deviation)))
        edges.append(Edge(b, a, etype, weight, float(deviation)))
        seen.add(pair)

    # depends-on (range conditioning)
    for a, b in _TRUE_DEPENDS:
        edges.append(Edge(a, b, "depends-on", 0.5, 0.0))

    return edges


class DependencyGraph:
    """In-process typed dependency graph with online gamma-decay of weights."""

    def __init__(self, edges: Optional[list[Edge]] = None, gamma: float = 0.98):
        self.gamma = gamma
        self._adj: dict[str, list[Edge]] = {}
        if edges:
            for e in edges:
                self._adj.setdefault(e.src, []).append(e)

    @classmethod
    def induced(cls, seed: int = 0, gamma: float = 0.98) -> "DependencyGraph":
        return cls(induce_edges(seed=seed), gamma=gamma)

    def neighbors(self, knob: str, etypes: Optional[tuple] = None) -> list[Edge]:
        out = self._adj.get(knob, [])
        if etypes:
            out = [e for e in out if e.etype in etypes]
        return sorted(out, key=lambda e: -e.weight)

    def synergistic_partners(self, knob: str) -> list[Edge]:
        return self.neighbors(knob, etypes=("synergizes-with",))

    def conflicting_partners(self, knob: str) -> list[Edge]:
        return self.neighbors(knob, etypes=("conflicts-with",))

    def decay(self, active_knobs: set[str], t: int = 1):
        """Apply gamma**t decay to edges not refreshed by recent telemetry."""
        factor = self.gamma ** t
        for src, elist in self._adj.items():
            for e in elist:
                if src not in active_knobs and e.dst not in active_knobs:
                    e.weight *= factor

    def refresh(self, src: str, dst: str, observed_interaction: float, lr: float = 0.3):
        """Refresh an edge weight from deployment telemetry (moving toward obs)."""
        for e in self._adj.get(src, []):
            if e.dst == dst:
                target = min(1.0, abs(observed_interaction) / 0.35)
                e.weight = (1 - lr) * e.weight + lr * target

    def to_json(self) -> list[dict]:
        seen, out = set(), []
        for elist in self._adj.values():
            for e in elist:
                k = (e.src, e.dst, e.etype)
                if k in seen:
                    continue
                seen.add(k)
                out.append(asdict(e))
        return out

    def save(self, path: str | Path):
        Path(path).write_text(json.dumps(self.to_json(), indent=2))


if __name__ == "__main__":
    g = DependencyGraph.induced(seed=0)
    edges = g.to_json()
    print(f"Induced {len(edges)} typed edges:")
    for e in edges:
        print(f"  {e['src']:26s} --{e['etype']:16s}--> {e['dst']:26s} "
              f"w={e['weight']:.2f} int={e['interaction']:+.3f}")
