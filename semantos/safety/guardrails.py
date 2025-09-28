from typing import Dict, Any, List

BOUNDS = {
    "vm.dirty_background_ratio": (1, 20),
    "vm.dirty_ratio": (5, 60),
    "vm.swappiness": (0, 100),
    "net.core.somaxconn": (512, 65535),
    "net.core.netdev_max_backlog": (1000, 200000),
    "kernel.sched_latency_ns": (10_000_000, 48_000_000),
    "kernel.sched_min_granularity_ns": (1_000_000, 20_000_000),
    "kernel.numa_balancing": (0, 1),
}

def validate(plan: Dict[str, Any], constraints: Dict[str, Any]) -> List[str]:
    issues = []
    recs = plan.get("recommendations", [])
    # Helper getters
    def get_val(p):
        for r in recs:
            if r["param"] == p:
                return float(r["target"])
        return None

    for rec in recs:
        k, v = rec["param"], float(rec["target"])
        if k in BOUNDS:
            lo, hi = BOUNDS[k]
            if not (lo <= v <= hi):
                issues.append(f"Out of bounds: {k}={v} not in [{lo},{hi}]")
    # Relational constraints
    bg = get_val("vm.dirty_background_ratio")
    dr = get_val("vm.dirty_ratio")
    if bg is not None and dr is not None and dr < bg:
        issues.append("vm.dirty_ratio must be >= vm.dirty_background_ratio")
    min_g = get_val("kernel.sched_min_granularity_ns")
    lat = get_val("kernel.sched_latency_ns")
    if min_g is not None and lat is not None and min_g > lat:
        issues.append("sched_min_granularity must be <= sched_latency")
    return issues
