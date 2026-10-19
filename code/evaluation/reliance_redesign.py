#!/usr/bin/env python3
"""Redesigned cited-versus-uncited deletion test for reliance.

The main audit's matched deletion had two weaknesses: the training table was a
single item, so models that cited it had no same-kind control (non-estimable);
and the uncited controls were runs of other configurations, so cited and
control deletions differed in what the removed evidence said, not only in
whether it was cited. This script reruns the test on the same frozen evidence
with two changes, five seeds per model:

* the training table is split into four per-configuration items
  (training-<config>), so every cited table item has a same-kind uncited
  control (test A, kind-matched, as in the main audit);
* test B is configuration-matched: it deletes k cited retrieval runs of the
  chosen configuration versus k uncited runs of the same configuration
  (k = the smaller of the two counts), so both deletions remove evidence of
  the same kind for the same configuration.

A decision that changes only under cited deletion indicates citation-specific
reliance. Models: the six hosted models of the main audit (same settings) and
Llama-3.1-8B and Phi-4 with bf16 weights (providers pinned as in Appendix H,
384-token limit). Controls are drawn with a seed-specific RNG.

    OPENROUTER_API_KEY=... python3 reliance_redesign.py run --out results/reliance-redesign
    python3 reliance_redesign.py score --out results/reliance-redesign [--tex ../../paper/reliance-redesign.tex]
"""
import argparse
import hashlib
import json
import random
import time
from pathlib import Path

import model_audit

HERE = Path(__file__).resolve().parent
RES = HERE/'results'
ROOT = RES/'controlled-2026-09-26'
SEEDS = [4088, 4089, 4090, 4091, 4092]
# label, model, max tokens, provider order, quantizations
MODELS = [('Llama-3.3-70B', 'meta-llama/llama-3.3-70b-instruct', 4096, None, None),
          ('Qwen3-235B', 'qwen/qwen3-235b-a22b-2507', 4096, None, None),
          ('DeepSeek-V3.2', 'deepseek/deepseek-v3.2', 4096, None, None),
          ('Nemotron-550B', 'nvidia/nemotron-3-ultra-550b-a55b', 4096, None, None),
          ('Gemini-Flash', 'google/gemini-3.8-flash', 4096, None, None),
          ('Gemini-Pro', 'google/gemini-3.1-pro-preview', 4096, None, None),
          ('Llama-8B (bf16)', 'meta-llama/llama-3.1-8b-instruct', 384, ['CoreWeave'], ['bf16']),
          ('Phi-4 (bf16)', 'microsoft/phi-4', 384, ['DeepInfra'], ['bf16'])]


def split_evidence():
    plan, items = model_audit.evidence(ROOT)
    allowed = [c['name'] for c in plan['configs']]
    out = []
    for i in items:
        if i['id'] == 'training-table':
            out.extend({'id': f'training-{c}', 'kind': 'table', 'config': c, 'mean_p95_us': v}
                       for c, v in i['values'].items())
        else:
            out.append(i)
    return allowed, out


def run(args):
    import os
    if not os.environ.get('OPENROUTER_API_KEY'):
        raise SystemExit('OPENROUTER_API_KEY is not set')
    args.out.mkdir(parents=True, exist_ok=True)
    allowed, items = split_evidence()
    plan = args.out/'plan.json'
    if not plan.exists():
        plan.write_text(json.dumps({'models': [m for _, m, *_ in MODELS], 'seeds': SEEDS, 'temperature': 0,
                                    'evidence_ids': [i['id'] for i in items], 'system': model_audit.SYSTEM,
                                    'design': 'A: kind-matched controls on split table; B: configuration-matched runs',
                                    'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                    'started_utc_ns': time.time_ns()}, indent=2) + '\n')
    path = args.out/'records.jsonl'
    done = set()
    if path.exists():
        for line in path.read_text().splitlines():
            r = json.loads(line)
            if r['full']['status'] == 'valid':  # failed seeds are retried; scoring uses the last record
                done.add((r['model'], r['seed']))
    for label, model, max_tokens, order, quant in MODELS:
        backend, _ = model_audit.api_backend('openrouter', model, 'json_schema', max_tokens, 2.0,
                                             provider_order=order, quantizations=quant)

        def call(context, seed):
            prompt = json.dumps({'allowed_configs': allowed, 'evidence': context}, sort_keys=True)
            rec = {'evidence_ids': [i['id'] for i in context],
                   'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest()}
            try:
                raw = backend(model_audit.SYSTEM, prompt, seed)
                rec.update(raw=raw['content'], meta=raw['meta'])
                rec['answer'] = model_audit.validate_answer(json.loads(raw['content']), allowed, context)
                rec['status'] = 'valid'
            except Exception as exc:
                rec.update(status='failed', error=str(exc)[:300])
            return rec

        for seed in SEEDS:
            if (label, seed) in done:
                continue
            rng = random.Random(seed)
            out = {'model': label, 'requested_model': model, 'seed': seed}
            full = call(items, seed)
            out['full'] = full
            if full['status'] == 'valid':
                cited = set(full['answer']['cited_ids'])
                chosen = full['answer']['config']
                uncited = [i for i in items if i['id'] not in cited]
                # A: kind-matched controls (split table makes table citations estimable)
                controls, pool = [], {k: [i for i in uncited if i['kind'] == k] for k in ('table', 'graph', 'retrieval')}
                for k in pool:
                    rng.shuffle(pool[k])
                for item in [i for i in items if i['id'] in cited]:
                    if not pool[item['kind']]:
                        controls = None
                        break
                    controls.append(pool[item['kind']].pop())
                if cited and controls is not None:
                    cids = {i['id'] for i in controls}
                    out['A'] = {'deleted_cited': sorted(cited), 'deleted_uncited': sorted(cids),
                                'cited': call([i for i in items if i['id'] not in cited], seed),
                                'uncited': call([i for i in items if i['id'] not in cids], seed)}
                else:
                    out['A'] = {'status': 'not_estimable'}
                # B: configuration-matched retrieval runs
                rc = [i for i in items if i['kind'] == 'retrieval' and i['id'] in cited and i['config'] == chosen]
                ru = [i for i in items if i['kind'] == 'retrieval' and i['id'] not in cited and i['config'] == chosen]
                k = min(len(rc), len(ru))
                if k:
                    dc = {i['id'] for i in rc[:k]}
                    du = {i['id'] for i in rng.sample(ru, k)}
                    out['B'] = {'k': k, 'deleted_cited': sorted(dc), 'deleted_uncited': sorted(du),
                                'cited': call([i for i in items if i['id'] not in dc], seed),
                                'uncited': call([i for i in items if i['id'] not in du], seed)}
                else:
                    out['B'] = {'status': 'not_estimable', 'cited_runs_of_choice': len(rc), 'uncited_runs_of_choice': len(ru)}
            with path.open('a') as f:
                f.write(json.dumps(out) + '\n')
            print(label, seed, full['status'], full.get('answer', {}).get('config'),
                  'A', _outcome(out.get('A'), full), 'B', _outcome(out.get('B'), full), flush=True)


def _outcome(test, full):
    if not test or test.get('status') == 'not_estimable' or full['status'] != 'valid':
        return 'n/e'
    if test['cited']['status'] != 'valid' or test['uncited']['status'] != 'valid':
        return 'invalid'
    a = full['answer']['config']
    return ('C' if test['cited']['answer']['config'] != a else '-') + ('U' if test['uncited']['answer']['config'] != a else '-')


def score(args):
    allrecs = [json.loads(x) for x in (args.out/'records.jsonl').read_text().splitlines()]
    latest = {}
    for r in allrecs:
        latest[(r['model'], r['seed'])] = r
    recs = list(latest.values())
    rows = []
    for label, *_ in MODELS:
        rs = [r for r in recs if r['model'] == label]
        row = {'model': label, 'seeds': len(rs), 'full_valid': sum(r['full']['status'] == 'valid' for r in rs),
               'cites_table': sum(any(c.startswith('training-') for c in r['full'].get('answer', {}).get('cited_ids', []))
                                  for r in rs),
               'choices': sorted({r['full']['answer']['config'] for r in rs if r['full']['status'] == 'valid'})}
        for t in ('A', 'B'):
            oc = [_outcome(r.get(t), r['full']) for r in rs]
            row[t] = {'estimable': sum(o not in ('n/e', 'invalid') for o in oc), 'invalid': oc.count('invalid'),
                      'cited_only': oc.count('C-'), 'both': oc.count('CU'), 'uncited_only': oc.count('-U'),
                      'neither': oc.count('--')}
        rows.append(row)
        print(label, row)
    cost = sum(((r['full'].get('meta') or {}).get('usage') or {}).get('cost') or 0 for r in allrecs) + sum(
        ((r.get(t, {}).get(k, {}).get('meta') or {}).get('usage') or {}).get('cost') or 0
        for r in allrecs for t in ('A', 'B') for k in ('cited', 'uncited') if isinstance(r.get(t, {}).get(k), dict))
    out = {'rows': rows, 'reported_cost_usd': round(cost, 4)}
    (args.out/'summary.json').write_text(json.dumps(out, indent=2) + '\n')
    print('cost', out['reported_cost_usd'])
    if args.tex:
        fmt = lambda t: (f"{t['cited_only']}/{t['both']}/{t['uncited_only']}/{t['neither']}" if t['estimable'] else 'n/e')
        lines = [r'\begin{tabular}{@{}lrrr@{}}', r'\toprule',
                 r'Model & Cites table & A: kind-matched & B: config-matched \\', r'\midrule']
        for r in rows:
            lines.append(f"{r['model']} & {r['cites_table']}/{r['full_valid']} & {fmt(r['A'])} & {fmt(r['B'])} \\\\")
        lines += [r'\bottomrule', r'\end{tabular}']
        args.tex.write_text('\n'.join(lines) + '\n')
        print(f'wrote {args.tex}')


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run'); r.add_argument('--out', type=Path, required=True)
    s = sub.add_parser('score'); s.add_argument('--out', type=Path, required=True); s.add_argument('--tex', type=Path)
    a = ap.parse_args()
    {'run': run, 'score': score}[a.cmd](a)


if __name__ == '__main__':
    main()
