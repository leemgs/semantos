"""Aggregate independently collected SemantOS hardware runs.

This program deliberately has no response simulator and no manuscript targets.
Its only input is immutable, run-level CSV exported by the experiment runner.
It validates provenance before producing summaries; it never manufactures rows.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import math
import json
import statistics
from collections import defaultdict
from pathlib import Path

REQUIRED = {
    "run_id", "timestamp_utc", "workload_family", "workload", "server_id",
    "kernel_release", "git_commit", "method", "split", "repetition",
    "window_count", "anomaly_count", "median_ms", "p95_ms", "p99_ms",
    "throughput", "unsafe_proposals", "veto_count", "rollback_count", "raw_log_sha256",
}
ALLOWED_SPLITS = {"train", "validation", "calibration", "test"}


def load_runs(path: Path, raw_log_dir: Path | None = None) -> list[dict]:
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
        if any(not r.get(key) for key in REQUIRED):
            raise ValueError('required provenance field is empty')
        if r["split"] not in ALLOWED_SPLITS:
            raise ValueError(f"invalid split for {r['run_id']}: {r['split']}")
        windows, anomalies = int(r["window_count"]), int(r["anomaly_count"])
        if windows <= 0 or not 0 <= anomalies <= windows:
            raise ValueError(f"invalid anomaly denominator for {r['run_id']}")
        digest = r['raw_log_sha256']
        if len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError(f"invalid raw-log digest for {r['run_id']}")
        if raw_log_dir is not None:
            raw = (raw_log_dir / digest).read_bytes()
            if hashlib.sha256(raw).hexdigest() != digest:
                raise ValueError(f"raw-log hash mismatch for {r['run_id']}")
        r["anomaly_rate"] = anomalies / windows
        for key in ("median_ms", "p95_ms", "p99_ms", "throughput"):
            r[key] = float(r[key])
            if not math.isfinite(r[key]) or r[key] < 0:
                raise ValueError(f'invalid {key}')
        if not r['median_ms'] <= r['p95_ms'] <= r['p99_ms']:
            raise ValueError('latency quantiles are out of order')
        for key in ('unsafe_proposals', 'veto_count', 'rollback_count', 'repetition'):
            if int(r[key]) < 0:
                raise ValueError(f'negative {key}')
    return rows


def aggregate(rows: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for row in rows:
        if row["split"] == "test":
            groups[(row["method"], row["workload_family"], row["workload"],
                    row['server_id'], row['kernel_release'])].append(row)
    if not groups:
        raise ValueError("no test rows; results may only be computed from split=test")
    output = []
    for key, rs in sorted(groups.items()):
        item = dict(zip(("method", "workload_family", "workload", 'server_id', 'kernel_release'), key))
        item["n_runs"] = len(rs)
        for metric in ("median_ms", "p95_ms", "p99_ms", "throughput"):
            xs = [r[metric] for r in rs]
            item[metric] = statistics.fmean(xs)
            item[f"{metric}_ci95"] = (1.96 * statistics.stdev(xs) / len(xs) ** .5
                                               if len(xs) > 1 else None)
        item["anomaly_count"] = sum(int(r["anomaly_count"]) for r in rs)
        item["window_count"] = sum(int(r["window_count"]) for r in rs)
        item["anomaly_rate"] = item["anomaly_count"] / item["window_count"]
        # A CI for an unweighted mean of run rates would not estimate this
        # pooled ratio when run denominators differ. Do not report that CI.
        item['anomaly_rate_ci95'] = None
        item['uncertainty_method'] = 'latency/throughput: normal approximation across runs; pooled anomaly CI not estimated'
        item["unsafe_proposals"] = sum(int(r["unsafe_proposals"]) for r in rs)
        item["veto_count"] = sum(int(r["veto_count"]) for r in rs)
        item["rollback_count"] = sum(int(r["rollback_count"]) for r in rs)
        output.append(item)
    return output


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_csv", type=Path)
    parser.add_argument("--output", type=Path, default=Path("reproduce/results/summary.json"))
    parser.add_argument('--raw-log-dir', type=Path, help='content-addressed files named by raw_log_sha256')
    args = parser.parse_args(argv)
    rows = load_runs(args.raw_csv, args.raw_log_dir)
    result = {
        "source": str(args.raw_csv),
        "source_sha256": hashlib.sha256(args.raw_csv.read_bytes()).hexdigest(),
        "definition": "anomaly_rate = sum(anomaly_count) / sum(window_count) per method/workload/server/kernel group",
        'raw_logs_verified': args.raw_log_dir is not None,
        "groups": aggregate(rows),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"validated {len(rows)} raw runs; wrote {args.output}")


if __name__ == "__main__":
    main()
