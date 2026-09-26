"""Aggregate independently collected SemantOS hardware runs.

This program deliberately has no response simulator and no manuscript targets.
Its only input is immutable, run-level CSV exported by the experiment runner.
It validates provenance before producing summaries; it never manufactures rows.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

REQUIRED = {
    "run_id", "timestamp_utc", "workload_family", "workload", "server_id",
    "kernel_release", "git_commit", "method", "split", "repetition",
    "window_count", "anomaly_count", "median_ms", "p95_ms", "p99_ms",
    "throughput", "unsafe_proposals", "veto_count", "rollback_count",
}
ALLOWED_SPLITS = {"train", "validation", "calibration", "test"}


def load_runs(path: Path) -> list[dict]:
    data = path.read_bytes()
    if not data:
        raise ValueError("raw input is empty")
    rows = list(csv.DictReader(data.decode("utf-8").splitlines()))
    if not rows:
        raise ValueError("raw input contains no runs")
    missing = REQUIRED - set(rows[0])
    if missing:
        raise ValueError(f"missing columns: {', '.join(sorted(missing))}")
    ids = [r["run_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("run_id values must be unique")
    for r in rows:
        if r["split"] not in ALLOWED_SPLITS:
            raise ValueError(f"invalid split for {r['run_id']}: {r['split']}")
        windows, anomalies = int(r["window_count"]), int(r["anomaly_count"])
        if windows <= 0 or not 0 <= anomalies <= windows:
            raise ValueError(f"invalid anomaly denominator for {r['run_id']}")
        if not r["raw_log_sha256"]:
            raise ValueError(f"missing raw-log digest for {r['run_id']}")
        r["anomaly_rate"] = anomalies / windows
        for key in ("median_ms", "p95_ms", "p99_ms", "throughput"):
            r[key] = float(r[key])
    return rows


def aggregate(rows: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for row in rows:
        if row["split"] == "test":
            groups[(row["method"], row["workload_family"], row["workload"])].append(row)
    if not groups:
        raise ValueError("no test rows; results may only be computed from split=test")
    output = []
    for key, rs in sorted(groups.items()):
        item = dict(zip(("method", "workload_family", "workload"), key))
        item["n_runs"] = len(rs)
        for metric in ("median_ms", "p95_ms", "p99_ms", "throughput"):
            xs = [r[metric] for r in rs]
            item[metric] = statistics.fmean(xs)
            item[f"{metric}_ci95"] = (1.96 * statistics.stdev(xs) / len(xs) ** .5
                                               if len(xs) > 1 else None)
        anomaly_rates = [r["anomaly_rate"] for r in rs]
        item["anomaly_count"] = sum(int(r["anomaly_count"]) for r in rs)
        item["window_count"] = sum(int(r["window_count"]) for r in rs)
        item["anomaly_rate"] = item["anomaly_count"] / item["window_count"]
        item["anomaly_rate_ci95"] = (
            1.96 * statistics.stdev(anomaly_rates) / len(anomaly_rates) ** .5
            if len(anomaly_rates) > 1 else None
        )
        item["unsafe_proposals"] = sum(int(r["unsafe_proposals"]) for r in rs)
        item["veto_count"] = sum(int(r["veto_count"]) for r in rs)
        item["rollback_count"] = sum(int(r["rollback_count"]) for r in rs)
        output.append(item)
    return output


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_csv", type=Path)
    parser.add_argument("--output", type=Path, default=Path("reproduce/results/summary.json"))
    args = parser.parse_args(argv)
    rows = load_runs(args.raw_csv)
    result = {
        "source": str(args.raw_csv),
        "source_sha256": hashlib.sha256(args.raw_csv.read_bytes()).hexdigest(),
        "definition": "anomaly_rate = sum(anomaly_count) / sum(window_count) per run",
        "groups": aggregate(rows),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"validated {len(rows)} raw runs; wrote {args.output}")


if __name__ == "__main__":
    main()
