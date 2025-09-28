from dataclasses import dataclass
from typing import List

@dataclass
class Tunable:
    key: str
    low: float
    high: float
    step: float
    unit: str
    note: str

# Minimal catalog used by the reasoning engine.
CATALOG: List[Tunable] = [
    Tunable("kernel.sched_latency_ns", 10_000_000, 48_000_000, 1_000_000, "ns", "CFS target latency"),
    Tunable("kernel.sched_min_granularity_ns", 2_000_000, 12_000_000, 500_000, "ns", "CFS min granularity"),
    Tunable("vm.dirty_background_ratio", 2, 15, 1, "%", "Background writeback threshold"),
    Tunable("vm.dirty_ratio", 10, 40, 1, "%", "Hard writeback threshold"),
    Tunable("net.core.somaxconn", 1024, 65535, 256, "", "Listen backlog"),
    Tunable("net.core.netdev_max_backlog", 1000, 100000, 1000, "packets", "Driver backlog"),
    Tunable("kernel.numa_balancing", 0, 1, 1, "bool", "NUMA auto balancing"),
    Tunable("vm.swappiness", 0, 100, 1, "", "Swapping aggressiveness"),
]
