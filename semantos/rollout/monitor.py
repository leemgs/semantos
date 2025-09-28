import random
from typing import Dict, Any

def check_regressions(prev_p95: float) -> Dict[str, Any]:
    # Synthetic post-change measurement (improves slightly on average)
    new_p95 = prev_p95 * random.uniform(0.86, 0.98)
    return {"post_p95_ms": new_p95, "regression": new_p95 > prev_p95}
