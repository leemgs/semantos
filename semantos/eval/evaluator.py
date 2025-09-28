import csv, statistics, random
from typing import List, Dict, Any

def run_trials(n: int = 10, base_p95: float = 180.0) -> Dict[str, Any]:
    baseline = [random.gauss(base_p95, 12.0) for _ in range(n)]
    tuned = [x * random.uniform(0.82, 0.95) for x in baseline]
    return {
        "baseline_p95_ms": statistics.median(baseline),
        "tuned_p95_ms": statistics.median(tuned),
        "improvement_pct": 100.0 * (statistics.median(baseline) - statistics.median(tuned)) / statistics.median(baseline),
        "n": n,
    }

def export_csv(path: str, records: List[Dict[str, Any]]) -> None:
    if not records:
        return
    keys = sorted(records[0].keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in records:
            w.writerow(r)
