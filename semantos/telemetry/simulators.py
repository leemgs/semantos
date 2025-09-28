import random
from typing import Dict

def simulate_telemetry(seed: int = 42, baseline_p95: float = 180.0) -> Dict[str, float]:
    random.seed(seed)
    return {
        "p95_ms": baseline_p95 * random.uniform(0.9, 1.1),
        "irq_rate": random.randint(8_000, 28_000),
        "load": round(random.uniform(4.0, 12.0), 2),
    }
