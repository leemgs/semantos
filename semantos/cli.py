import json, argparse, os
from .telemetry.simulators import simulate_telemetry
from .kb.store import KBStore
from .reasoning.engine import plan
from .safety.guardrails import validate
from .safety.sandbox import SandboxSysctl
from .safety.privileged import SysctlApplier
from .rollout.planner import staggered_batches
from .rollout.applier import apply_batches
from .rollout.monitor import check_regressions
from .eval.evaluator import run_trials, export_csv

def main():
    ap = argparse.ArgumentParser(description="SemantOS Reproduction Pipeline")
    ap.add_argument("--kb", default="experiments/kb", help="KB path")
    ap.add_argument("--sandbox", default="experiments/sandbox/sysctl.conf", help="Sandbox sysctl file")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--trials", type=int, default=12)
    ap.add_argument("--applier", choices=["sandbox","sysctl"], default="sandbox", help="How to apply recommendations")
    ap.add_argument("--apply", action="store_true", help="Actually write to /proc/sys (requires root). Omit for dry-run.")
    ap.add_argument("--rollback", action="store_true", help="Rollback using last backup (requires root, sysctl mode).")
    args = ap.parse_args()

    # Rollback path (sysctl mode)
    if args.rollback:
        app = SysctlApplier()
        changed = app.rollback()
        print("[ROLLBACK] Restored values:")
        for k, prev, after in changed:
            print(f" - {k}: set -> {after} (from backup {prev})")
        return

    # 1) Telemetry
    tel = simulate_telemetry(seed=args.seed)

    # 2) Context/Constraints
    ctx = {"hardware": "AMD EPYC 7763", "workload": "Web Serving", "telemetry": tel}
    cons = {"SLO_p95_ms": 120.0, "guardrails": ["no_oom", "no_starvation", "bounded_changes"]}

    # 3) KB store (collect experience)
    kb = KBStore(args.kb)
    kb.put_experience("telemetry", {"telemetry": tel})

    # 4) Reasoning
    proposal = plan(ctx, cons)

    # 5) Safety checks
    issues = validate(proposal, cons)
    if issues:
        print("[GUARDRAILS] Violations detected:")
        for i in issues:
            print(" -", i)
        print("Aborting rollout due to guardrail violations.")
        return

    # 6) Rollout batches + Apply
    batches = staggered_batches(proposal["recommendations"], batch_size=3)

    if args.applier == "sandbox":
        sandbox = SandboxSysctl(args.sandbox)
        apply_batches(batches, sandbox.apply)
    else:
        # sysctl mode: dry-run or real apply
        app = SysctlApplier()
        # Flatten batches for a single atomic-ish pass per batch for clarity
        for idx, b in enumerate(batches, 1):
            print(f"[SYSCTL] Batch {idx}:")
            changes = app.apply(b, apply=args.apply)
            for k, old, new in changes:
                mode = "APPLY" if args.apply else "DRY-RUN"
                print(f" - {mode}: {k}: {old} -> {new}")

    # 7) Post-check and evaluation
    post = check_regressions(tel["p95_ms"])
    result = run_trials(n=args.trials, base_p95=tel["p95_ms"])

    # 8) Export results
    os.makedirs("experiments/results", exist_ok=True)
    export_csv("experiments/results/summary.csv", [{
        "baseline_p95_ms": result["baseline_p95_ms"],
        "tuned_p95_ms": result["tuned_p95_ms"],
        "improvement_pct": result["improvement_pct"],
        "trials": result["n"],
        "post_p95_ms": post["post_p95_ms"],
        "regression": post["regression"],
    }])

    print("[OK] Pipeline complete.")
    print("Telemetry:", tel)
    print("Recommendations:", json.dumps(proposal["recommendations"], indent=2))
    print("Evaluation summary written to experiments/results/summary.csv")

if __name__ == "__main__":
    main()
