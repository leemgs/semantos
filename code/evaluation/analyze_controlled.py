"""Validate raw controlled measurements and derive all reported tables."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import statistics
import sys

from controlled_kernel import digest, misses, quantile, write
from safety_counts import summarize
from validate_split import validate


def interval(values):
    # Exactly ten run/block units in this predeclared experiment.
    if len(values) != 10:
        raise ValueError('ten blocks required')
    return {'mean': statistics.mean(values),
            'ci95_halfwidth': 2.2621571628540993 * statistics.stdev(values) / len(values)**.5}


def analyze(root):
    for name, expected in json.loads((root / 'SHA256SUMS.json').read_text()).items():
        if digest(root / name) != expected:
            raise ValueError('hash mismatch: ' + name)
    plan = json.loads((root / 'plan.json').read_text())
    frozen = json.loads((root / 'frozen.json').read_text())
    gate = json.loads((root / 'gate.json').read_text())
    split = json.loads((root / 'split.json').read_text())
    validate(split)
    rows = [json.loads(s) for s in (root / 'runs.jsonl').read_text().splitlines()]
    ids = [r['id'] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate run')
    expected = {(role, ms*1000000, b, c['name'])
                for role, periods in list(plan['roles_ms'].items()) + [('staged', [5, 8])]
                for ms in periods for b in range(plan['blocks']) for c in plan['configs']}
    if set((r['role'], r['period_ns'], r['block'], r['name']) for r in rows) != expected:
        raise ValueError('incomplete acquisition')
    by_id = {r['id']: r for r in rows}
    for r in split['records']:
        raw = by_id[r['id']]
        if r['role'] != raw['role'] or r['sha256'] != hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest():
            raise ValueError('source lineage mismatch')
    train_ids = {r['id'] for r in rows if r['role'] == 'train'}
    cal_ids = {r['id'] for r in rows if r['role'] == 'calibration'}
    if set(frozen['source_ids']) != train_ids or set(gate['source_ids']) != cal_ids:
        raise ValueError('frozen artifact has forbidden source')
    if gate['score_sha256'] != digest(root / 'frozen.json'):
        raise ValueError('score changed after calibration')
    for c in plan['configs']:
        train = [by_id[i] for i in train_ids if by_id[i]['name'] == c['name']]
        actual_mean = statistics.mean(quantile(r['events']) for r in train)
        actual_score = statistics.mean(misses(r['events'], plan['deadline_ns'])/len(r['events']) for r in train)
        if actual_mean != frozen['means_p95_us'][c['name']] or actual_score != frozen['score'][c['name']]:
            raise ValueError('training statistic mismatch')
    if frozen['selected']['empirical_min'] != min(frozen['means_p95_us'], key=frozen['means_p95_us'].get):
        raise ValueError('selector mismatch')
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'safety-runtime'))
    from safety_core import conformal_threshold
    calibration = [by_id[i] for i in sorted(cal_ids)]
    labels = [misses(r['events'], plan['deadline_ns'])/len(r['events']) > plan['unsafe_fraction'] for r in calibration]
    scores = [frozen['score'][r['name']] for r in calibration]
    expected_tau = {str(a): conformal_threshold(scores, labels, a) for a in plan['alphas']}
    if gate['thresholds'] != expected_tau or gate['unsafe_n'] != sum(labels):
        raise ValueError('calibration mismatch')
    test = [r for r in rows if r['role'] == 'test']
    if max(by_id[i]['ended_utc_ns'] for i in train_ids) > frozen['frozen_utc_ns']:
        raise ValueError('selection predates training completion')
    if frozen['frozen_utc_ns'] >= min(by_id[i]['started_utc_ns'] for i in cal_ids):
        raise ValueError('score not frozen before calibration')
    if max(by_id[i]['ended_utc_ns'] for i in cal_ids) > gate['frozen_utc_ns'] or gate['frozen_utc_ns'] >= min(r['started_utc_ns'] for r in test):
        raise ValueError('gate not frozen between calibration and test')
    for r in rows:
        target = {k: r[k] for k in ('slack_ns', 'cpus')}
        if r['applied_readback'] != target or r['restored_readback'] != r['old'] or not r['restored']:
            raise ValueError('setting/restoration mismatch')
        events = r.get('events', [e for s in r['stages'] for e in s['events']])
        if not events or any(e['lateness_ns'] != max(0, e['observed_ns'] - e['target_ns']) for e in events):
            raise ValueError('invalid event arithmetic')
        if r['role'] != 'staged' and len(events) != plan['samples']:
            raise ValueError('incomplete samples')
        if r['role'] == 'staged':
            for i, s in enumerate(r['stages']):
                if len(s['events']) != plan['stage_samples'][i] or s['misses'] != misses(s['events'], plan['deadline_ns']):
                    raise ValueError('stage record mismatch')
                if i < len(r['stages'])-1 and s['misses']/len(s['events']) > plan['unsafe_fraction']:
                    raise ValueError('promoted breached stage')
            breach = r['stages'][-1]['misses']/len(r['stages'][-1]['events']) > plan['unsafe_fraction']
            if breach != r['rolled_back'] or r['completed'] == breach:
                raise ValueError('stage stop mismatch')
            if not breach and len(r['stages']) != len(plan['stage_samples']):
                raise ValueError('premature completion')
    configs = [c['name'] for c in plan['configs']]
    comparisons, safety, staging = [], [], []
    traces = []
    for ms in plan['roles_ms']['test']:
        lookup = {(r['block'], r['name']): r for r in test if r['period_ns'] == ms*1000000}
        rng = random.Random(plan['seed'] + ms)
        random_choices = [rng.choice(configs) for _ in range(plan['blocks'])]
        choices = {method: [name]*plan['blocks'] for method, name in frozen['selected'].items()}
        choices['seeded_random'] = random_choices
        for method, selected in choices.items():
            picked = [lookup[b, name] for b, name in enumerate(selected)]
            baseline = [lookup[b, configs[0]] for b in range(plan['blocks'])]
            absolute = [quantile(r['events']) for r in picked]
            paired = [100*(1-quantile(r['events'])/quantile(c['events'])) for r, c in zip(picked, baseline)]
            comparisons.append({'period_ms': ms, 'method': method,
                                'p95_us': interval(absolute), 'reduction_pct': interval(paired),
                                'misses': sum(misses(r['events'], plan['deadline_ns']) for r in picked),
                                'events': sum(len(r['events']) for r in picked),
                                'scope': 'shared-outcome replay, not independent controller execution'})
            for r in picked:
                traces.append({'method': method, 'run_id': r['id'], 'chosen_config': r['name'],
                               'selection_artifact_sha256': digest(root/'frozen.json'),
                               'objective': plan['objective'], 'score': frozen['score'][r['name']],
                               'observed_p95_us': quantile(r['events']), 'evaluation_mode': 'offline_replay'})
        for alpha, tau in gate['thresholds'].items():
            candidates = [r for r in test if r['period_ns'] == ms*1000000]
            labeled = [{'bundle_id': r['id'], 'decision': 'accepted' if frozen['score'][r['name']] < tau else 'vetoed',
                        'unsafe': misses(r['events'], plan['deadline_ns'])/len(r['events']) > plan['unsafe_fraction'],
                        'rolled_back': False} for r in candidates]
            safety.append({'period_ms': ms, 'alpha': float(alpha), 'tau': tau,
                           'unsafe_calibration_n': gate['unsafe_n'], **summarize(labeled),
                           'scope': 'gate replay on independent observed outcomes; no deployment prevented'})
        stages = [r for r in rows if r['role'] == 'staged' and r['period_ns'] == ms*1000000]
        staging.append({'period_ms': ms, 'applied': len(stages),
                        'completed': sum(r['completed'] for r in stages),
                        'rolled_back': sum(r['rolled_back'] for r in stages),
                        'restored': sum(r['restored'] for r in stages),
                        'events': sum(len(s['events']) for r in stages for s in r['stages']),
                        'misses': sum(s['misses'] for r in stages for s in r['stages']),
                        'exposure_ms': sum(r['exposure_ns'] for r in stages)/1e6,
                        'rollback_precision': None,
                        'scope': 'fresh separate executions, outcome-triggered stops; no independent action-level ground truth'})
    output = {'comparisons': comparisons, 'safety_replay': safety, 'staged_execution': staging,
              'frozen': frozen, 'costs': json.loads((root/'costs.json').read_text()),
              'runs': len(rows), 'grid_events': sum(len(r.get('events', [])) for r in rows),
              'llm_status': plan['llm_status'],
              'scope': plan['scope'], 'input_hashes_sha256': digest(root/'SHA256SUMS.json')}
    write(root/'analysis.json', output)
    with (root/'decision-traces.jsonl').open('w') as f:
        for trace in traces:
            f.write(json.dumps(trace)+'\n')
    lines = ['# Controlled per-thread experiment', '', plan['scope'], '',
             'Policy comparisons are offline replay on the same held-out grid, not live LLM execution.', '',
             '| Period ms | Policy | P95 us ± 95% CI | Paired reduction % ± 95% CI | Misses/events |',
             '|---|---|---|---|---|']
    tex = [r'\begin{tabular}{rlrr}', r'\toprule', r'Period & Selector & P95 ($\mu$s) & Misses \\', r'\midrule']
    for r in comparisons:
        q, g = r['p95_us'], r['reduction_pct']
        lines.append(f"| {r['period_ms']} | {r['method']} | {q['mean']:.1f} ± {q['ci95_halfwidth']:.1f} | {g['mean']:.1f} ± {g['ci95_halfwidth']:.1f} | {r['misses']}/{r['events']} |")
        tex.append(f"{r['period_ms']} & {r['method'].replace('_', ' ')} & {q['mean']:.1f} & {r['misses']}/{r['events']} \\\\")
    tex += [r'\bottomrule', r'\end{tabular}']
    (root/'table.tex').write_text('\n'.join(tex)+'\n')
    lines += ['', 'Safety replay (TP=veto unsafe; FP=veto safe; FN=accept unsafe; TN=accept safe):', '',
              '| Period | alpha | tau | TP | FP | FN | TN |', '|---|---|---|---|---|---|---|']
    for r in safety:
        c = r['counts']
        lines.append(f"| {r['period_ms']} | {r['alpha']} | {r['tau']:.3f} | {c['tp']} | {c['fp']} | {c['fn']} | {c['tn']} |")
    lines += ['', 'Actual staged executions:', '', '| Period | Applied | Completed | Stopped/restored | Total restored | Misses/events |', '|---|---|---|---|---|---|']
    for r in staging:
        lines.append(f"| {r['period_ms']} | {r['applied']} | {r['completed']} | {r['rolled_back']} | {r['restored']} | {r['misses']}/{r['events']} |")
    lines += ['', 'No recovery deadline, rollback precision, host-generalization or LLM advantage is inferred.',
              'Student-t intervals are descriptive across ten shared-host blocks; no multiplicity correction.',
              'Costs and complete traces are in analysis.json and decision-traces.jsonl.']
    (root/'summary.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))
    return output


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('root', type=Path)
    analyze(p.parse_args().root)
