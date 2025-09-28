from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Constraints:
    SLO_p95_ms: float = 120.0
    guardrails: List[str] = field(default_factory=lambda: ["no_oom", "no_starvation", "bounded_changes"])

@dataclass
class Context:
    hardware: str = "AMD EPYC 7763"
    workload: str = "Web Serving"
    telemetry: Dict[str, float] = field(default_factory=lambda: {"p95_ms": 180.0, "irq_rate": 15000, "load": 6.0})

@dataclass
class ExperimentConfig:
    context: Context = field(default_factory=Context)
    constraints: Constraints = field(default_factory=Constraints)
