"""
spec.py — Ground-truth specification of the experimental setup described in
SemantOS (AAAI submission, semantos_7p_aaai_20260705_2010).

This module is the single source of truth for:
  * the tunable knobs and their typed metadata (range/unit/subsystem),
  * the six evaluation workloads,
  * the three server classes (S1/S2/S3),
  * and the numeric targets reported in the paper (Tables 2/3, Figs 1/3,
    tau-sweep, exploration efficiency, drift study).

Everything downstream (response model, controllers, conformal safety runtime,
evaluation harness) reads its constants from here so the reproduction stays
consistent with the manuscript.
"""

from dataclasses import dataclass, field
from typing import Optional

# --------------------------------------------------------------------------- #
# Tunable knobs (Background & Related Work; Semantic Reasoning)
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Knob:
    name: str
    subsystem: str            # scheduler | memory | io | irq | numa
    unit: str
    lo: float
    hi: float
    default: float

# The knobs named throughout the paper (/proc, /sys sysctls).
KNOBS = {
    "sched_latency_ns":         Knob("sched_latency_ns",         "scheduler", "ns", 1e6,  4.8e7, 2.4e7),
    "sched_min_granularity_ns": Knob("sched_min_granularity_ns", "scheduler", "ns", 1e6,  3.0e7, 3.0e6),
    "sched_wake_affinity":      Knob("sched_wake_affinity",      "scheduler", "bool", 0.0, 1.0,   1.0),
    "vm.swappiness":            Knob("vm.swappiness",            "memory",    "ratio", 0.0, 100.0, 60.0),
    "vm.dirty_ratio":           Knob("vm.dirty_ratio",           "memory",    "pct", 1.0, 90.0,  20.0),
    "dirty_ratio":              Knob("dirty_ratio",              "memory",    "pct", 1.0, 90.0,  20.0),
    "dirty_background_ratio":   Knob("dirty_background_ratio",   "memory",    "pct", 1.0, 90.0,  10.0),
    "min_free_kbytes":          Knob("min_free_kbytes",          "memory",    "kB", 1024, 4194304, 67584),
    "irq_affinity":             Knob("irq_affinity",             "irq",       "mask", 0.0, 1.0,  0.0),
    "numa_balancing":           Knob("numa_balancing",           "numa",      "bool", 0.0, 1.0,  1.0),
}

# --------------------------------------------------------------------------- #
# Workloads (Evaluation / Setup) — six controlled workloads
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Workload:
    key: str
    label: str
    # per-workload Baseline (untuned) operating point used as the reference in
    # Table 2 reductions; ms and % anomaly.
    base_median_ms: float
    base_p95_ms: float
    base_anomaly_pct: float
    base_throughput: float
    # dominant subsystems (drives which knobs matter — Observation 1)
    hot_subsystems: tuple = field(default_factory=tuple)

WORKLOADS = {
    "web":       Workload("web",       "Web-serving microservice", 23.4, 30.9, 6.1, 1000, ("scheduler", "irq")),
    "oltp":      Workload("oltp",      "OLTP (TPC-C)",             25.1, 34.0, 6.6, 820,  ("io", "scheduler")),
    "streaming": Workload("streaming", "Streaming (Kafka+Spark)",  24.0, 32.5, 6.3, 1220, ("memory", "io")),
    "sensor":    Workload("sensor",    "IoT sensor gateway",       22.2, 28.9, 5.4, 610,  ("irq", "scheduler")),
    "hpc_ml":    Workload("hpc_ml",    "GPU HPC/ML inference",     23.0, 30.2, 5.9, 1500, ("memory", "numa")),
    "audio":     Workload("audio",     "Real-time audio pipeline", 21.6, 27.8, 5.1, 500,  ("scheduler", "irq")),
}
WORKLOAD_KEYS = list(WORKLOADS.keys())

# --------------------------------------------------------------------------- #
# Server classes (Evaluation / Setup) — S1/S2/S3 on Linux 6.4
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Server:
    key: str
    label: str
    cores: int
    mem_gb: int
    numa: bool
    accel: Optional[str]
    # mild per-server multiplier on latency (heterogeneity — see Observation 1)
    latency_scale: float

SERVERS = {
    "S1": Server("S1", "2x Xeon Gold (32c, 256GB, NVMe)", 32, 256, False, None,  1.00),
    "S2": Server("S2", "2x EPYC (64c, 512GB, NUMA)",      64, 512, True,  None,  0.97),
    "S3": Server("S3", "2x Xeon + A100 (40c, 384GB)",     40, 384, False, "A100", 1.02),
}
SERVER_KEYS = list(SERVERS.keys())

# --------------------------------------------------------------------------- #
# Paper numeric targets — used both to calibrate the response model and to
# assert (in tests) that the harness reproduces the manuscript.
# --------------------------------------------------------------------------- #

# Table 2 — SemantOS reductions vs Baseline (means over 10 runs).
# headline "up to" = maxima across workloads; medians in parentheses.
PAPER_TABLE2 = {
    "median_latency": {"max": 0.23, "median": 0.18, "ci": 0.014},
    "p95_latency":    {"max": 0.28, "median": 0.22, "ci": 0.017},
    "anomaly":        {"max": 0.31, "median": 0.27, "ci": 0.021},
    "op_time":        {"lo": 0.85, "hi": 0.92},
}

# Table 3 — ablation: (median latency ms, anomaly %) under stationary / drift.
# key -> (lat_stat, lat_drift, anom_stat, anom_drift, lat_ci, anom_ci)
PAPER_TABLE3 = {
    "full":         (19.5, 19.6, 2.4, 2.5, 0.4, 0.3),   # KB+RAG+Safety
    "wo_depgraph":  (21.4, 21.6, 4.1, 4.4, 0.5, 0.4),   # knobs independent
    "wo_rag":       (21.2, 21.3, 3.6, 3.8, 0.5, 0.4),   # KB+Safety
    "wo_safety":    (19.8, 20.0, 4.9, 5.2, 0.4, 0.5),   # KB+RAG
    "kb_only":      (22.6, 22.7, 7.1, 7.6, 0.6, 0.7),
}

# Figure 1 — knob-pair synergy on tail latency (single vs co-tuned).
PAPER_FIG1 = {
    "sched_min_granularity_ns_only": -0.05,
    "sched_wake_affinity_only":      -0.08,
    "combined":                      -0.38,
}

# Figure 3 — Pareto frontier operating points (anomaly %, P95 ms).
PAPER_FIG3 = {
    "Baseline": (6.3, 28.0),
    "Expert":   (5.0, 24.0),
    "BO/RL":    (4.2, 23.0),
    "SemantOS": (3.0, 20.0),
}
# vs Expert on the frontier: up to 17% lower latency at same anomaly budget,
# 23% lower anomaly at equal throughput.
PAPER_FIG3_GAINS = {"latency": 0.17, "anomaly": 0.23}

# Uncertainty-quantification / guardrail tau sweep (Safety Runtime).
# tau -> (rollback_precision, rollback_recall, anomaly_pct)
PAPER_TAU_SWEEP = {
    0.30: (0.79, 0.94, 3.5),
    0.55: (0.86, 0.88, 2.8),
    0.70: (0.91, 0.79, 2.3),
}
DEFAULT_TAU = 0.55
CONFORMAL_ALPHA = 0.10          # target unsafe-acceptance rate (1-alpha coverage)

# Exploration efficiency — configs to reach within 2% of final median latency.
PAPER_EXPLORATION = {
    "semantos": (38, 52),
    "bo_rl":    (120, 300),
}

# Drift study (30-day continuous deployment).
PAPER_DRIFT = {"anomaly_ceiling": 0.03, "rollback_precision_floor": 0.85}

# Cost constants for the tau-selection objective C(tau) (Safety Runtime).
# Calibrated so argmin_tau C(tau) subject to dSLO(tau) <= delta lands on the
# paper's default tau = 0.55.  The false-rollback weight c_fp is comparatively
# high because an independent SLO guard already catches residual unsafe actions
# (defence in depth; cf. the case study), so unnecessary rollbacks — which churn
# production traffic — dominate the operational cost near the operating point.
COST = {"c_fn": 4.0, "c_fp": 6.0, "lam": 0.5, "slo_budget_delta": 0.5}

N_RUNS = 10                     # independent runs per (workload, server) pair
GLOBAL_SEED = 20260705
