from typing import Dict, Any
from .prompts import SYSTEM
from ..kb.schema import CATALOG

def _clip(key: str, val: float) -> float:
    for t in CATALOG:
        if t.key == key:
            return min(max(val, t.low), t.high)
    return val

def plan(context: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic 'LLM-like' stub: rule-based reasoning that mirrors paper logic.
    """
    tel = context.get("telemetry", {})
    p95 = float(tel.get("p95_ms", 200.0))
    irq = float(tel.get("irq_rate", 15000))
    load = float(tel.get("load", 6.0))
    target = float(constraints.get("SLO_p95_ms", 120.0))

    # Heuristics
    backlog = 4096 if irq > 18000 else 2048
    somax = 32768 if load > 8 else 16384
    sched_lat = 18_000_000 if load > 8 else 24_000_000
    min_gran = 3_000_000 if load > 8 else 4_000_000
    dirty_bg = 8 if p95 > target else 5
    dirty = 25 if p95 > target else 15
    swappiness = 10 if p95 > target else 30

    recs = [
        {"param": "net.core.netdev_max_backlog", "action": "set", "target": _clip("net.core.netdev_max_backlog", backlog)},
        {"param": "net.core.somaxconn", "action": "set", "target": _clip("net.core.somaxconn", somax)},
        {"param": "kernel.sched_latency_ns", "action": "set", "target": _clip("kernel.sched_latency_ns", sched_lat)},
        {"param": "kernel.sched_min_granularity_ns", "action": "set", "target": _clip("kernel.sched_min_granularity_ns", min_gran)},
        {"param": "vm.dirty_background_ratio", "action": "set", "target": _clip("vm.dirty_background_ratio", dirty_bg)},
        {"param": "vm.dirty_ratio", "action": "set", "target": _clip("vm.dirty_ratio", dirty)},
        {"param": "vm.swappiness", "action": "set", "target": _clip("vm.swappiness", swappiness)},
        {"param": "kernel.numa_balancing", "action": "set", "target": 1 if load > 5 else 0},
    ]

    rationale = [
        "Increase network queues to absorb bursts when IRQ rate is high.",
        "Tune CFS latency/granularity to reduce context-switch overhead under load.",
        "Lower dirty thresholds to smooth writeback and reduce tail latency.",
        "Keep swappiness moderate to avoid IO stalls.",
        "Enable NUMA balancing for cross-node locality under moderate-to-high load."
    ]

    return {"recommendations": recs, "rationale": rationale, "system_prompt": SYSTEM}
