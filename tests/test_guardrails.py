from semantos.safety.guardrails import validate

def test_bounds_ok():
    plan = {"recommendations": [
        {"param": "vm.dirty_background_ratio", "action":"set", "target": 8},
        {"param": "vm.dirty_ratio", "action":"set", "target": 25},
        {"param": "vm.swappiness", "action":"set", "target": 30},
        {"param": "kernel.sched_latency_ns", "action":"set", "target": 20000000},
        {"param": "kernel.sched_min_granularity_ns", "action":"set", "target": 4000000},
    ]}
    issues = validate(plan, {"SLO_p95_ms":120.0})
    assert issues == []
