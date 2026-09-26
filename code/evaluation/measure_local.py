"""Bounded local microbenchmarks with raw measured timings (no target values).

These are baseline measurements, not the paper's six workloads, controller
comparisons, or kernel-tuning gains. All work files live below --out.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import sqlite3
import time
import zlib
from inventory import inventory


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--runs',type=int,default=10)
    p.add_argument('--operations',type=int,default=100)
    args=p.parse_args()
    if not 2 <= args.runs <= 100 or not 10 <= args.operations <= 10000:
        p.error('runs must be 2..100 and operations 10..10000')
    args.out.mkdir(parents=True,exist_ok=False)
    source=Path(__file__).read_bytes()
    env=inventory()
    # Predeclared deadline is a benchmark rule, not inferred from measurements.
    manifest={'kind':'measured_local_baseline','schema_version':1,'environment':env,
              'runs':args.runs,'operations_per_run':args.operations,'warmup_operations':10,
              'deadline_ms':50.0,'seed':4088,'clock':'perf_counter_ns',
              'controller':'unchanged_kernel_baseline','intervention':'none',
              'sqlite':sqlite3.sqlite_version,'zlib':zlib.ZLIB_VERSION,
              'source_sha256':hashlib.sha256(source).hexdigest(),
              'limitations':['single shared host','no kernel writes','no LLM','not TPC-C, Kafka/Spark or GPU inference',
                             'closed-loop load; no correction for coordinated omission','no host isolation or cache drop']}
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    payload=random.Random(4088).randbytes(65536)
    schedule=[(w,r) for r in range(args.runs) for w in ['sqlite_commit','file_fsync','zlib_compress']]
    random.Random(4088).shuffle(schedule)
    with (args.out/'operations.csv').open('w',newline='') as f:
        fields=['workload','run','operation','latency_ms','error','deadline_ms','started_unix_ns']
        out=csv.DictWriter(f,fieldnames=fields);out.writeheader()
        for workload,run in schedule:
            path=args.out/f'work-{workload}-{run}'
            conn=None;fd=None
            if workload=='sqlite_commit':
                conn=sqlite3.connect(path)
                conn.execute('PRAGMA journal_mode=WAL'); conn.execute('PRAGMA synchronous=FULL')
                conn.execute('CREATE TABLE items (id INTEGER PRIMARY KEY, value BLOB)');conn.commit()
            elif workload=='file_fsync':fd=os.open(path,os.O_CREAT|os.O_RDWR,0o600)
            for i in range(-10,args.operations):
                started=time.time_ns(); t=time.perf_counter_ns();error=False
                try:
                    if conn is not None:
                        conn.execute('INSERT INTO items(value) VALUES (?)',(payload[:4096],));conn.commit()
                    elif fd is not None:
                        os.lseek(fd,0,os.SEEK_SET)
                        data=memoryview(payload)
                        while data:
                            n=os.write(fd,data);data=data[n:]
                        os.fsync(fd)
                    else:
                        compressed=zlib.compress(payload,6)
                        if zlib.decompress(compressed)!=payload:raise RuntimeError('round trip mismatch')
                except Exception:
                    error=True
                elapsed=(time.perf_counter_ns()-t)/1e6
                if i>=0:out.writerow(dict(workload=workload,run=run,operation=i,latency_ms=elapsed,
                                         error=int(error),deadline_ms=50.0,started_unix_ns=started))
            if conn is not None:conn.close()
            if fd is not None:os.close(fd)
            path.unlink(missing_ok=True)
            f.flush()
            print(f'measured {workload} run {run+1}/{args.runs}',flush=True)
    manifest['raw_sha256']=hashlib.sha256((args.out/'operations.csv').read_bytes()).hexdigest()
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
