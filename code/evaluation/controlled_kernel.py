"""Prospective, bounded per-thread experiment; no host-global sysctl writes.

Compare frozen non-LLM selectors by replay on the same measured held-out grid.
Separately execute a staged intervention with restoration in fresh child processes.
Neither component is a measurement of LLM superiority or production safety.
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
import statistics
import subprocess
import sys
import time


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def snapshot():
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl.restype = ctypes.c_long
    slack = libc.prctl(30, 0, 0, 0, 0)
    if slack < 0:
        raise OSError(ctypes.get_errno(), 'PR_GET_TIMERSLACK')
    return {'slack_ns': slack, 'cpus': sorted(os.sched_getaffinity(0))}


def set_bundle(target):
    if target['slack_ns'] not in (50000, 1000000) or not target['cpus']:
        raise ValueError('unsupported experiment configuration')
    restore(target)


def restore(target):
    # Restore both controls even if one restoration operation fails.
    libc = ctypes.CDLL(None, use_errno=True)
    errors = []
    if libc.prctl(29, ctypes.c_ulong(target['slack_ns']), 0, 0, 0):
        errors.append(OSError(ctypes.get_errno(), 'PR_SET_TIMERSLACK'))
    try:
        os.sched_setaffinity(0, target['cpus'])
    except OSError as exc:
        errors.append(exc)
    if errors:
        raise errors[0]
    if snapshot() != {k: target[k] for k in ('slack_ns', 'cpus')}:
        raise RuntimeError('bundle readback mismatch')


def observe(period_ns, count, warmup=0):
    start = time.monotonic_ns()
    events = []
    for i in range(count + warmup):
        target = start + (i + 1) * period_ns
        remaining = target - time.monotonic_ns()
        if remaining > 0:
            time.sleep(remaining / 1e9)
        observed = time.monotonic_ns()
        if i >= warmup:
            events.append({'target_ns': target, 'observed_ns': observed,
                           'lateness_ns': max(0, observed - target)})
    return events


def quantile(events, q=.95):
    return sorted(e['lateness_ns'] / 1000 for e in events)[math.ceil(q * len(events)) - 1]


def misses(events, deadline):
    return sum(e['lateness_ns'] > deadline for e in events)


def child(case):
    old = snapshot()
    row = {**case, 'old': old, 'started_utc_ns': time.time_ns(), 'stages': []}
    started = time.monotonic_ns()
    try:
        set_bundle(case)
        row['applied_readback'] = snapshot()
        if case['role'] == 'staged':
            row['rolled_back'] = False
            for count in case['stage_samples']:
                events = observe(case['period_ns'], count)
                n = misses(events, case['deadline_ns'])
                row['stages'].append({'events': events, 'misses': n})
                if n / count > case['unsafe_fraction']:
                    row['rolled_back'] = True
                    break
            row['completed'] = not row['rolled_back']
        else:
            row['events'] = observe(case['period_ns'], case['samples'], case['warmup'])
    finally:
        row['exposure_ns'] = time.monotonic_ns() - started
        restore(old)
        row['restored_readback'] = snapshot()
        row['restored'] = row['restored_readback'] == old
    row['ended_utc_ns'] = time.time_ns()
    return row


def freeze(rows, plan, out):
    # Only train and retrieval exist at this point; calibration/test are unopened.
    train = [r for r in rows if r['role'] == 'train']
    configs = plan['configs']
    means = {c['name']: statistics.mean(quantile(r['events']) for r in train
                                      if r['name'] == c['name']) for c in configs}
    scores = {c['name']: statistics.mean(misses(r['events'], plan['deadline_ns']) / len(r['events'])
                                       for r in train if r['name'] == c['name']) for c in configs}
    names = [c['name'] for c in configs]
    # Saturated two-factor representation: exactly the same four measured means.
    b, a, d, joint = [means[n] for n in names]
    interaction = joint - a - d + b
    predicted = dict(zip(names, [b, b + (a-b), b + (d-b), b+(a-b)+(d-b)+interaction]))
    selected = {'control': names[0], 'empirical_min': min(means, key=means.get),
                'graph_min': min(predicted, key=predicted.get)}
    from induce_graph import induce
    sweeps = []
    for block in range(plan['blocks']):
        block_rows = [r for r in train if r['block'] == block]
        values = {r['name']: quantile(r['events']) for r in block_rows}
        sweeps.append({'id': f'train-sweep-{block}', 'run': block, 'split': 'train',
                       'source': 'measured', 'group': 'period-2ms-single-host',
                       'pair': ['timer_slack', 'cpu_affinity'],
                       'losses': dict(zip(['baseline', 'a', 'b', 'joint'], [values[n] for n in names]))})
    frozen = {'means_p95_us': means, 'score': scores, 'selected': selected,
              'interaction_us': interaction, 'edges': induce(sweeps),
              'source_ids': [r['id'] for r in train], 'frozen_utc_ns': time.time_ns(),
              'scope': 'same measured table; graph is a reparameterization, not extra evidence'}
    write(out / 'frozen.json', frozen)
    return frozen


def run(out):
    if out.exists():
        raise ValueError('output directory must be new')
    out.mkdir(parents=True)
    cpus = sorted(os.sched_getaffinity(0))
    configs = [{'name': f's{s}_a{a}', 'slack_ns': s, 'cpus': cpus if a == 'all' else cpus[:1]}
               for s in (50000, 1000000) for a in ('all', 'one')]
    plan = {'seed': 4090, 'blocks': 10, 'samples': 40, 'warmup': 5,
            'deadline_ns': 200000, 'unsafe_fraction': .1, 'stage_samples': [8, 16, 32],
            'roles_ms': {'train': [2], 'retrieval': [3], 'calibration': [4], 'test': [5, 8]},
            'alphas': [.05, .1, .2], 'configs': configs, 'clock': 'monotonic_ns',
            'kernel': platform.release(), 'python': platform.python_version(),
            'cpuinfo': Path('/proc/cpuinfo').read_text().split('model name')[1].split('\n')[0].strip(),
            'created_utc_ns': time.time_ns(), 'source_sha256': digest(__file__),
            'support_hashes': {p: digest(Path(__file__).parent / p) for p in
                               ['induce_graph.py', 'validate_split.py', '../safety-runtime/safety_core.py']},
            'base_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
            'scope': 'single shared host, one periodic workload family; period-disjoint roles, no host/family holdout',
            'policy_comparison': 'paired offline replay on common measured outcomes; zero online search trials',
            'objective': 'minimize mean training run P95; no energy objective',
            'llm_status': 'not_run: local model socket forbidden; no configured external model credential'}
    write(out / 'plan.json', plan)
    rng = random.Random(plan['seed'])
    rows, costs = [], {}
    frozen = None
    with (out / 'runs.jsonl').open('w') as stream:
        for role, periods in list(plan['roles_ms'].items()) + [('staged', [5, 8])]:
            before = time.monotonic()
            if role == 'calibration':
                tick = time.monotonic()
                frozen = freeze(rows, plan, out)
                costs['graph_and_selection_seconds'] = time.monotonic() - tick
            if role == 'test':
                sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'safety-runtime'))
                from safety_core import conformal_threshold
                cal = [r for r in rows if r['role'] == 'calibration']
                u = [frozen['score'][r['name']] for r in cal]
                y = [misses(r['events'], plan['deadline_ns']) / len(r['events']) > plan['unsafe_fraction'] for r in cal]
                write(out / 'gate.json', {'frozen_utc_ns': time.time_ns(), 'source_ids': [r['id'] for r in cal],
                      'unsafe_n': sum(y), 'thresholds': {str(a): conformal_threshold(u, y, a) for a in plan['alphas']},
                      'score_sha256': digest(out / 'frozen.json')})
            for block in range(plan['blocks']):
                cases = [{**c, 'role': role, 'block': block, 'period_ns': period * 1000000,
                          'id': f'{role}-{period}-{block}-{c["name"]}',
                          **{k: plan[k] for k in ('samples', 'warmup', 'deadline_ns', 'unsafe_fraction', 'stage_samples')}}
                         for period in periods for c in configs]
                rng.shuffle(cases)
                for case in cases:
                    response = subprocess.run([sys.executable, '-B', __file__, '--child', json.dumps(case)],
                                              check=True, capture_output=True, text=True, timeout=15)
                    row = json.loads(response.stdout)
                    rows.append(row)
                    stream.write(json.dumps(row, allow_nan=False) + '\n'); stream.flush()
            costs[role + '_seconds'] = time.monotonic() - before
            print(role + ' complete', flush=True)
    write(out / 'costs.json', costs)
    # Each source is a separately acquired run, with its own content hash.
    records = [{'id': r['id'], 'role': r['role'], 'group': f'period-{r["period_ns"]}',
                'sha256': hashlib.sha256(json.dumps(r, sort_keys=True).encode()).hexdigest()}
               for r in rows if r['role'] != 'staged']
    artifacts = [{'kind': kind, 'sources': [r['id'] for r in records if r['role'] == role]}
                 for kind, role in [('graph', 'train'), ('retrieval_index', 'retrieval'),
                                    ('calibrator', 'calibration'), ('evaluation', 'test')]]
    manifest = {'records': records, 'artifacts': artifacts,
                'scope': 'period-disjoint within one family/host, not family/hardware independence'}
    from validate_split import validate
    write(out / 'split.json', manifest)
    write(out / 'split-check.json', validate(manifest))
    write(out / 'SHA256SUMS.json', {p.name: digest(p) for p in out.iterdir() if p.is_file()})


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path)
    p.add_argument('--child')
    args = p.parse_args()
    if args.child:
        print(json.dumps(child(json.loads(args.child)), allow_nan=False))
    elif args.out:
        run(args.out)
    else:
        p.error('--out or --child required')
