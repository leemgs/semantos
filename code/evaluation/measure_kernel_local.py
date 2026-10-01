"""Bounded real per-process Linux intervention; never writes host sysctls.

Each case runs in a fresh child. Predeclared training chooses a configuration;
subsequent held-out paired blocks estimate its effect against explicit control.
"""
import argparse
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import subprocess
import sys
import time


def child(case):
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(29, ctypes.c_ulong(case['slack_ns']), 0, 0, 0):
        raise OSError(ctypes.get_errno(), 'PR_SET_TIMERSLACK')
    os.sched_setaffinity(0, case['cpus'])
    actual = libc.prctl(30, 0, 0, 0, 0)
    if actual != case['slack_ns'] or sorted(os.sched_getaffinity(0)) != case['cpus']:
        raise RuntimeError('kernel readback mismatch')
    start = time.monotonic_ns()
    rows = []
    for i in range(case['warmup'] + case['samples']):
        target = start + (i + 1) * case['period_ns']
        remaining = target - time.monotonic_ns()
        if remaining > 0:
            time.sleep(remaining / 1e9)
        observed = time.monotonic_ns()
        if i >= case['warmup']:
            rows.append({'event': i-case['warmup'], 'target_ns': target,
                         'observed_ns': observed, 'lateness_ns': max(0, observed-target)})
    return {**case, 'readback_slack_ns': actual, 'readback_cpus': sorted(os.sched_getaffinity(0)), 'events': rows}


def p95(row):
    values = sorted(e['lateness_ns'] for e in row['events'])
    return values[math.ceil(.95*len(values))-1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--child')
    p.add_argument('--out', type=Path)
    a = p.parse_args()
    if a.child:
        print(json.dumps(child(json.loads(a.child))))
        return
    if not a.out or a.out.exists():
        p.error('--out must be a new directory')
    a.out.mkdir(parents=True)
    cpus = sorted(os.sched_getaffinity(0))
    configs = [{'name': f'slack{slack}_{affinity}', 'slack_ns': slack,
                'cpus': cpus if affinity == 'all' else cpus[:1]}
               for slack in [50000, 1000000] for affinity in ['all', 'one']]
    plan = {'seed':4088, 'periods_ns':[2000000,5000000], 'train_blocks':5,
            'test_blocks':10, 'samples':80, 'warmup':10, 'deadline_ns':200000,
            'control':'slack50000_all', 'selection':'lowest mean training run P95 per period',
            'configs':configs, 'cpu':platform.processor(), 'kernel':platform.release(),
            'python':platform.python_version(), 'clock':'monotonic_ns',
            'scope':'single host, owned child process, no external competing load'}
    (a.out/'plan.json').write_text(json.dumps(plan, indent=2)+'\n')
    rng = random.Random(plan['seed'])
    rows = []
    with (a.out/'runs.jsonl').open('w') as stream:
        for role, blocks in [('train',5), ('test',10)]:
            if role == 'test':
                selected = {str(period): min(configs, key=lambda c: sum(p95(r) for r in rows if r['period_ns']==period and r['name']==c['name'])/5)['name'] for period in plan['periods_ns']}
                (a.out/'frozen-selection.json').write_text(json.dumps(selected,indent=2)+'\n')
            for block in range(blocks):
                cases = [{**c, 'role':role,'block':block,'period_ns':period,
                          'samples':80,'warmup':10} for period in plan['periods_ns'] for c in configs]
                rng.shuffle(cases)
                for case in cases:
                    result = subprocess.run([sys.executable,__file__,'--child',json.dumps(case)],check=True,capture_output=True,text=True,timeout=10)
                    row=json.loads(result.stdout); rows.append(row)
                    stream.write(json.dumps(row)+'\n'); stream.flush()
            print(role+' completed',flush=True)
    hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in a.out.iterdir()}
    (a.out/'SHA256SUMS.json').write_text(json.dumps(hashes,indent=2)+'\n')

if __name__ == '__main__':
    main()
