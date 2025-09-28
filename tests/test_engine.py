from semantos.reasoning.engine import plan

def test_plan_keys():
    ctx = {"hardware":"AMD EPYC 7763", "workload":"Web", "telemetry":{"p95_ms":180,"irq_rate":20000,"load":9}}
    cons = {"SLO_p95_ms": 120.0, "guardrails":["no_oom"]}
    p = plan(ctx, cons)
    assert "recommendations" in p and isinstance(p["recommendations"], list)
    assert any(r["param"]=="net.core.somaxconn" for r in p["recommendations"])
