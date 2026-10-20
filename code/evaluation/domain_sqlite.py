#!/usr/bin/env python3
"""A second domain: SQLite durability and journal settings.

Configuration advice for databases is the setting of much LLM tuning work, so
this script repeats the audit on a database task measured for this purpose.
Four configurations cross SQLite's `synchronous` setting (NORMAL or OFF) with
its journal mode (DELETE, the default, or WAL). The objective is
the P95 commit latency of small write transactions (10 rows of 100 bytes each).
Each run is a fresh child process with a fresh database file: 10 warm-up and
200 measured transactions. Three data roles are separated in time: training
(10 blocks), retrieval (10 blocks) and held-out test (10 blocks). The four
configurations are randomized within each block. The plan is written before
measurement and test runs never enter a prompt.

Unlike the kernel task, the labels are descriptive and model priors about
SQLite are informative but can mislead: a pilot showed the two WAL settings
close and overlapping (OFF is not reliably faster than NORMAL), and DELETE
with NORMAL an order of magnitude slower. The six hosted models answer the main audit's prompt and schema,
with only the objective changed, under the full evidence and with no
evidence. Choices are scored by paired replay on the test blocks against the
table selector's choice. Explanations are scored with the automatic checks of
evidence_instances.py; they have no verified labels.

    python3 domain_sqlite.py measure --out results/domain-sqlite
    OPENROUTER_API_KEY=... python3 domain_sqlite.py run --out results/domain-sqlite
    python3 domain_sqlite.py score --out results/domain-sqlite [--tex ../../paper/domain-sqlite.tex]
"""
import argparse
import csv
import hashlib
import json
import math
import os
import platform
import random
import re
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIGS = {'sync_normal_delete': ('NORMAL', 'DELETE'), 'sync_normal_wal': ('NORMAL', 'WAL'),
           'sync_off_delete': ('OFF', 'DELETE'), 'sync_off_wal': ('OFF', 'WAL')}
ROLES = [('train', 10), ('retrieval', 10), ('test', 10)]
WARMUP, TXNS, ROWS = 10, 200, 10
SEED = 4088
SYSTEM = ('Select one allowed config to minimize SQLite write-transaction P95 commit latency. Return JSON with config '
          '(exact allowed name), cited_ids (evidence IDs), and explanation. Evidence contains measured training '
          'summaries and retrieval runs, not held-out test outcomes. Do not invent evidence.')


def child(sync, journal, workdir):
    """One run: fresh database, WARMUP + TXNS write transactions; prints per-transaction latencies in ns."""
    path = os.path.join(workdir, 'bench.db')
    con = sqlite3.connect(path, isolation_level=None)
    con.execute(f'PRAGMA journal_mode={journal}')
    con.execute(f'PRAGMA synchronous={sync}')
    con.execute('CREATE TABLE t (id INTEGER PRIMARY KEY, payload BLOB)')
    payload = os.urandom(100)
    lat = []
    for i in range(WARMUP + TXNS):
        t0 = time.perf_counter_ns()
        con.execute('BEGIN')
        con.executemany('INSERT INTO t (payload) VALUES (?)', [(payload,)] * ROWS)
        con.execute('COMMIT')
        if i >= WARMUP:
            lat.append(time.perf_counter_ns() - t0)
    readback = (con.execute('PRAGMA journal_mode').fetchone()[0], con.execute('PRAGMA synchronous').fetchone()[0])
    con.close()
    print(json.dumps({'lat_ns': lat, 'readback': readback}))


def p95_us(lat_ns):
    v = sorted(x/1000 for x in lat_ns)
    return round(v[math.ceil(.95*len(v)) - 1], 3)


def measure(args):
    args.out.mkdir(parents=True, exist_ok=True)
    plan_path = args.out/'plan.json'
    if (args.out/'runs.jsonl').exists():
        raise SystemExit('runs.jsonl exists; measurements are collected once')
    rng = random.Random(SEED)
    schedule = []
    for role, blocks in ROLES:
        for b in range(blocks):
            names = list(CONFIGS)
            rng.shuffle(names)
            schedule += [{'role': role, 'block': b, 'name': n} for n in names]
    plan = {'configs': CONFIGS, 'roles': ROLES, 'warmup': WARMUP, 'transactions': TXNS,
            'rows_per_transaction': ROWS, 'payload_bytes': 100, 'seed': SEED, 'objective': 'P95 commit latency, us',
            'selection_rule': 'minimum of the training table (mean training-run P95)', 'schedule': schedule,
            'sqlite_version': sqlite3.sqlite_version, 'python': platform.python_version(),
            'platform': platform.platform(), 'cpu_count': os.cpu_count(),
            'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'written_utc_ns': time.time_ns()}
    plan_path.write_text(json.dumps(plan, indent=2) + '\n')
    with (args.out/'runs.jsonl').open('w') as fh:
        for s in schedule:
            sync, journal = CONFIGS[s['name']]
            with tempfile.TemporaryDirectory(dir=args.workdir) as wd:
                t0 = time.time_ns()
                out = subprocess.run([sys.executable, __file__, 'child', sync, journal, wd], capture_output=True,
                                     text=True, check=True).stdout
            r = json.loads(out)
            row = {**s, 'id': f"{s['role']}-{s['block']}-{s['name']}", 'sync': sync, 'journal': journal,
                   'readback': r['readback'], 'started_utc_ns': t0, 'lat_ns': r['lat_ns'], 'p95_us': p95_us(r['lat_ns'])}
            fh.write(json.dumps(row) + '\n')
            print(row['id'], row['p95_us'], row['readback'], flush=True)
    digest = {n: hashlib.sha256((args.out/n).read_bytes()).hexdigest() for n in ('plan.json', 'runs.jsonl')}
    (args.out/'SHA256SUMS.json').write_text(json.dumps(digest, indent=2) + '\n')


def load(out):
    rows = [json.loads(x) for x in (out/'runs.jsonl').read_text().splitlines()]
    train = {}
    for r in rows:
        if r['role'] == 'train':
            train.setdefault(r['name'], []).append(r['p95_us'])
    table = {n: round(statistics.mean(train[n]), 3) for n in CONFIGS}
    items = [{'id': 'training-table', 'kind': 'table', 'values': table}]
    items += [{'id': r['id'], 'kind': 'retrieval', 'config': r['name'], 'block': r['block'],
               'transactions': TXNS, 'p95_us': r['p95_us']} for r in rows if r['role'] == 'retrieval']
    test = {}
    for r in rows:
        if r['role'] == 'test':
            test.setdefault(r['block'], {})[r['name']] = r['p95_us']
    return rows, items, test


def replay(test, name, ref):
    """Paired change of P95 versus ref over test blocks (percent, Student-t 95% half-width)."""
    d = [100*(b[name] - b[ref])/b[ref] for b in test.values()]
    m = statistics.mean(d)
    hw = 2.2621571628540993*statistics.stdev(d)/math.sqrt(len(d)) if len(d) > 1 and any(d) else 0.0
    return round(m, 1), round(hw, 1)


def run(args):
    import model_audit
    import prompt_robustness as pr
    key = os.environ.get('OPENROUTER_API_KEY')
    if not key:
        raise SystemExit('OPENROUTER_API_KEY is not set')
    _, items, _ = load(args.out)
    allowed = list(CONFIGS)
    path = args.out/'records.jsonl'
    done = set()
    if path.exists():
        for line in path.read_text().splitlines():
            r = json.loads(line)
            if r['status'] == 'valid':
                done.add((r['model'], r['variant'], r['seed']))
    (args.out/'llm-plan.json').write_text(json.dumps({'models': [m for _, _, m in pr.MODELS], 'seeds': pr.SEEDS,
                                                      'variants': ['full', 'model_only'], 'system': SYSTEM,
                                                      'temperature': 0, 'citation_cap': 6,
                                                      'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                                      'started_utc_ns': time.time_ns()}, indent=2) + '\n')
    last = [0.0]
    for name, _, model in pr.MODELS:
        for variant, ev in (('full', items), ('model_only', [])):
            prompt = json.dumps({'allowed_configs': allowed, 'evidence': ev}, sort_keys=True)
            for seed in pr.SEEDS:
                if (name, variant, seed) in done:
                    continue
                rec = {'model': name, 'requested_model': model, 'variant': variant, 'seed': seed, 'prompt': prompt}
                try:
                    raw, meta = pr.call(model, SYSTEM, prompt, 6, 0, seed, key, 2.0, last, urllib.request.urlopen)
                    rec.update(raw=raw, meta=meta)
                    answer = json.loads(raw)
                    model_audit.validate_answer(answer, allowed, ev)
                    if len(answer['cited_ids']) > 6:
                        raise ValueError('citation cap exceeded')
                    rec.update(answer=answer, status='valid')
                except Exception as exc:
                    rec.update(status='failed', error=str(exc)[:300])
                with path.open('a') as fh:
                    fh.write(json.dumps(rec) + '\n')
                print(name, variant, seed, rec['status'], rec.get('answer', {}).get('config'), flush=True)


def score(args):
    import evidence_instances as ei
    import mitigation_baseline as mb
    mb.CONFIGS = list(CONFIGS)  # range check: this domain's labels
    mb.CFG = re.compile('|'.join(CONFIGS), re.I)
    rows, items, test = load(args.out)
    f = ei.facts(items)
    latest = {}
    for line in (args.out/'records.jsonl').read_text().splitlines():
        r = json.loads(line)
        latest[(r['model'], r['variant'], r['seed'])] = r
    recs = list(latest.values())
    out = {'facts': f, 'selector': f['selector'], 'test_replay_vs_selector': {n: replay(test, n, f['selector']) for n in CONFIGS},
           'test_mean_p95_us': {n: round(statistics.mean(b[n] for b in test.values()), 3) for n in CONFIGS},
           'test_block_winners': {}, 'models': {}, 'invalid': sum(r['status'] != 'valid' for r in recs)}
    for b in test.values():
        w = min(b, key=b.get)
        out['test_block_winners'][w] = out['test_block_winners'].get(w, 0) + 1
    full_checks, review = [], []
    for name in sorted({r['model'] for r in recs}, key=lambda m: [x[0] for x in __import__('prompt_robustness').MODELS].index(m)):
        m = {}
        for variant in ('full', 'model_only'):
            rs = sorted((r for r in recs if r['model'] == name and r['variant'] == variant and r['status'] == 'valid'),
                        key=lambda r: r['seed'])
            m[variant] = [r['answer']['config'] for r in rs]
            if variant == 'full':
                for r in rs:
                    c = ei.check(r['answer'], items, f)
                    full_checks.append(c)
                    review.append({'model': name, 'seed': r['seed'], 'config': r['answer']['config'],
                                   'cited_ids': ' '.join(r['answer']['cited_ids']), 'overstated_proxy': c['overstated'],
                                   'range_errors': json.dumps(c['range_errors']),
                                   'unsupported_numbers': json.dumps(c['unsupported_numbers']),
                                   'explanation': r['answer']['explanation']})
        out['models'][name] = m
        print(name, m)
    agg = mb.aggregate(full_checks)
    agg['first_half'] = sum(c['first_half'] for c in full_checks)
    out['full_checks'] = agg
    out['reported_cost_usd'] = round(sum(((r.get('meta') or {}).get('usage') or {}).get('cost') or 0
                                         for r in map(json.loads, (args.out/'records.jsonl').read_text().splitlines())), 4)
    (args.out/'summary.json').write_text(json.dumps(out, indent=2) + '\n')
    with (args.out/'explanations-for-review.csv').open('w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(review[0]))
        w.writeheader()
        w.writerows(review)
    print(json.dumps({k: out[k] for k in ('selector', 'test_replay_vs_selector', 'test_mean_p95_us', 'test_block_winners', 'invalid')}))
    print(json.dumps(f))
    print(json.dumps(agg))
    if args.tex:
        short = {'sync_normal_delete': 'N/D', 'sync_normal_wal': 'N/W', 'sync_off_delete': 'O/D', 'sync_off_wal': 'O/W'}
        rep = out['test_replay_vs_selector']
        fmt = lambda cs: ' '.join(f"{short[c]}$^{{{cs.count(c)}}}$" for c in sorted(set(cs), key=list(CONFIGS).index)) or '--'
        lines = [r'\begin{tabular}{@{}lll@{}}', r'\toprule', r'Model & Full evidence & No evidence \\', r'\midrule',
                 f"Table selector & {short[f['selector']]} & -- \\\\"]
        for name, m in out['models'].items():
            lines.append(f"{name} & {fmt(m['full'])} & {fmt(m['model_only'])} \\\\")
        lines += [r'\midrule', r"\multicolumn{3}{@{}l@{}}{Test P95 vs.\ selector's choice (\%):} \\"]
        lines += [f"\\quad {short[c]} & ${rep[c][0]:+.1f}\\pm{rep[c][1]:.1f}$ & \\\\" for c in CONFIGS if c != f['selector']]
        lines += [r'\bottomrule', r'\end{tabular}']
        args.tex.write_text('\n'.join(lines) + '\n')
        print(f'wrote {args.tex}')


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'child':
        return child(*sys.argv[2:5])
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    m = sub.add_parser('measure'); m.add_argument('--out', type=Path, required=True)
    m.add_argument('--workdir', default=None, help='directory for the temporary database files (default: system temp)')
    r = sub.add_parser('run'); r.add_argument('--out', type=Path, required=True)
    s = sub.add_parser('score'); s.add_argument('--out', type=Path, required=True); s.add_argument('--tex', type=Path)
    a = ap.parse_args()
    {'measure': measure, 'run': run, 'score': score}[a.cmd](a)


if __name__ == '__main__':
    main()
