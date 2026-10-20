#!/usr/bin/env python3
"""Do the audit's findings hold beyond the single evidence set of the main audit?

The main audit gives every model one frozen evidence list (training table from
2 ms runs, 40 retrieval runs at 3 ms). This script reruns the six hosted models
with the same system prompt, schema, citation cap and settings (temperature 0,
five seeds) on three further evidence instances built only from training-side
data (no test outcome enters a prompt):

* I1 4ms     same training table, retrieval runs replaced by the 40
             calibration runs at 4 ms (different values, extremes and block
             winners);
* I2 relabel the main evidence with the four labels permuted
             (s50000_aall<->s1000000_aone, s50000_aone<->s1000000_aall), so the
             best configuration carries the name that suggests the worst
             setting;
* I3 session a separate measurement session on the same host (Appendix B
             temporal holdout): training table from its five 2 ms training
             blocks, retrieval items its 20 training runs at 5 ms.

The graph item is omitted (it is uninformative and removing it changed no
choice). Answers are scored with the automatic checks of mitigation_baseline.py
against each instance's own evidence; the quantifier proxy counts "consistently
/ always / all ... lowest" only when the chosen configuration is not lowest in
every block, and "significantly" always (the evidence contains no test). The
explanations are exported for review; they have no verified claim labels.

    OPENROUTER_API_KEY=... python3 evidence_instances.py run --out results/evidence-instances
    python3 evidence_instances.py score --out results/evidence-instances [--tex ../../paper/evidence-instances.tex]
"""
import argparse
import csv
import hashlib
import json
import re
import statistics
import time
import urllib.request
from pathlib import Path

import mitigation_baseline as mb
import model_audit
import prompt_robustness as pr
from controlled_kernel import quantile

HERE = Path(__file__).resolve().parent
RES = HERE/'results'
MAIN = RES/'controlled-2026-09-26'
SESSION = RES/'kernel-local-2026-09-26'
INSTANCES = ['4ms', 'relabel', 'session']
PERM = {'s50000_aall': 's1000000_aone', 's50000_aone': 's1000000_aall',
        's1000000_aall': 's50000_aone', 's1000000_aone': 's50000_aall'}
SESSION_NAMES = {'slack50000_all': 's50000_aall', 'slack50000_one': 's50000_aone',
                 'slack1000000_all': 's1000000_aall', 'slack1000000_one': 's1000000_aone'}
ALLOWED = ['s50000_aall', 's50000_aone', 's1000000_aall', 's1000000_aone']


def main_items():
    _, items = model_audit.evidence(MAIN)
    return [i for i in items if i['kind'] != 'graph']


def instance(name):
    """Evidence list for one instance, in the main audit's item format and order."""
    if name == 'main':
        return main_items()
    if name == '4ms':
        frozen = json.loads((MAIN/'frozen.json').read_text())
        rows = [json.loads(x) for x in (MAIN/'runs.jsonl').read_text().splitlines()]
        return [{'id': 'training-table', 'kind': 'table', 'values': frozen['means_p95_us']}] + [
            {'id': r['id'].replace('calibration-', 'retrieval-'), 'kind': 'retrieval', 'config': r['name'],
             'period_ns': r['period_ns'], 'p95_us': quantile(r['events'])} for r in rows if r['role'] == 'calibration']
    if name == 'relabel':
        out = []
        for i in main_items():
            if i['kind'] == 'table':
                out.append({**i, 'values': {PERM[c]: v for c, v in i['values'].items()}})
            else:
                out.append({**i, 'id': i['id'].replace(i['config'], PERM[i['config']]), 'config': PERM[i['config']]})
        return out
    if name == 'session':
        rows = [json.loads(x) for x in (SESSION/'runs.jsonl').read_text().splitlines()]
        train2 = [r for r in rows if r['role'] == 'train' and r['period_ns'] == 2000000]
        table = {}
        for r in train2:
            table.setdefault(SESSION_NAMES[r['name']], []).append(quantile(r['events']))
        items = [{'id': 'training-table', 'kind': 'table',
                  'values': {c: round(statistics.mean(table[c]), 4) for c in ALLOWED}}]
        for r in rows:  # file order = block order, randomized within block
            if r['role'] == 'train' and r['period_ns'] == 5000000:
                c = SESSION_NAMES[r['name']]
                items.append({'id': f"retrieval-5-{r['block']}-{c}", 'kind': 'retrieval', 'config': c,
                              'period_ns': r['period_ns'], 'p95_us': quantile(r['events'])})
        return items
    raise ValueError(name)


def facts(ev):
    table = next(i for i in ev if i['kind'] == 'table')['values']
    runs, blocks = {}, {}
    for i in ev:
        if i['kind'] == 'retrieval':
            runs.setdefault(i['config'], []).append(i['p95_us'])
            blocks.setdefault(i['id'].split('-')[2], {})[i['config']] = i['p95_us']
    wins = {}
    for b in blocks.values():
        c = min(b, key=b.get)
        wins[c] = wins.get(c, 0) + 1
    return {'selector': min(table, key=table.get), 'table': table, 'blocks': len(blocks), 'block_wins': wins,
            'min_max_mean': {c: [min(v), max(v), round(statistics.mean(v), 3)] for c, v in runs.items()}}


QUANT = re.compile(pr.OVERSTATE.pattern.split(r'|\bsignificantly')[0], re.I)
AVERAGE = re.compile(r'\b(?:average|mean|median|typical)\b', re.I)
SIGNIF = re.compile(r'\bsignificantly (?:lower|better|faster|higher|less)\b', re.I)


def check(answer, ev, f):
    c = mb.check(answer, ev)
    c['selector_choice'] = answer['config'] == f['selector']
    wins_all = f['block_wins'].get(answer['config'], 0) == f['blocks']
    expl = answer['explanation']
    quant = [m for m in QUANT.finditer(expl) if not AVERAGE.search(m.group(0))]  # "lowest average" is no regularity
    c['overstated'] = bool((quant and not wins_all) or SIGNIF.search(expl))
    cited = [i for i in ev if i['id'] in answer['cited_ids'] and i['kind'] == 'retrieval']
    order = [i['id'] for i in ev if i['kind'] == 'retrieval']
    c['first_half'] = sum(order.index(i['id']) < len(order)/2 for i in cited)
    return c


def run(args):
    import os
    key = os.environ.get('OPENROUTER_API_KEY')
    if not key:
        raise SystemExit('OPENROUTER_API_KEY is not set')
    args.out.mkdir(parents=True, exist_ok=True)
    system = model_audit.SYSTEM
    plan = args.out/'plan.json'
    if not plan.exists():
        plan.write_text(json.dumps({'models': [m for _, _, m in pr.MODELS], 'instances': INSTANCES, 'seeds': pr.SEEDS,
                                    'temperature': 0, 'max_tokens': 4096, 'citation_cap': 6, 'system': system,
                                    'response_format': 'strict json_schema', 'provider_require_parameters': True,
                                    'facts': {n: facts(instance(n)) for n in ['main'] + INSTANCES},
                                    'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                    'started_utc_ns': time.time_ns()}, indent=2) + '\n')
    path = args.out/'records.jsonl'
    done = set()
    if path.exists():
        for line in path.read_text().splitlines():
            r = json.loads(line)
            if r['status'] == 'valid':
                done.add((r['model'], r['instance'], r['seed']))
    last = [0.0]
    for name, _, model in pr.MODELS:
        for inst in INSTANCES:
            ev = instance(inst)
            prompt = json.dumps({'allowed_configs': ALLOWED, 'evidence': ev}, sort_keys=True)
            for seed in pr.SEEDS:
                if (name, inst, seed) in done:
                    continue
                rec = {'model': name, 'requested_model': model, 'instance': inst, 'seed': seed, 'prompt': prompt,
                       'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest()}
                try:
                    raw, meta = pr.call(model, system, prompt, 6, 0, seed, key, args.min_interval, last,
                                        urllib.request.urlopen)
                    rec.update(raw=raw, meta=meta)
                    answer = json.loads(raw)
                    model_audit.validate_answer(answer, ALLOWED, ev)
                    if len(answer['cited_ids']) > 6:
                        raise ValueError('citation cap exceeded')
                    rec.update(answer=answer, status='valid')
                except Exception as exc:
                    rec.update(status='failed', error=str(exc)[:300])
                with path.open('a') as fh:
                    fh.write(json.dumps(rec) + '\n')
                print(name, inst, seed, rec['status'], rec.get('answer', {}).get('config'), flush=True)


def score(args):
    latest = {}
    for line in (args.out/'records.jsonl').read_text().splitlines():
        r = json.loads(line)
        latest[(r['model'], r['instance'], r['seed'])] = r
    recs = list(latest.values())
    rows, per_model, review = [], {}, []
    for inst in ['main'] + INSTANCES:
        ev = instance(inst)
        f = facts(ev)
        if inst == 'main':  # the main audit's hosted full-context answers, same checks
            answers = [(n, s, a) for n, s, a, _ in mb.original_answers()]
            invalid = 0
        else:
            rs = [r for r in recs if r['instance'] == inst]
            answers = [(r['model'], r['seed'], r['answer']) for r in rs if r['status'] == 'valid']
            invalid = sum(r['status'] != 'valid' for r in rs)
        checks = [check(a, ev, f) for _, _, a in answers]
        agg = mb.aggregate(checks)
        agg.update(instance=inst, invalid=invalid, selector=f['selector'],
                   first_half=sum(c['first_half'] for c in checks),
                   chosen_wins_all_blocks=f['block_wins'].get(f['selector'], 0) == f['blocks'],
                   selector_block_wins=f"{f['block_wins'].get(f['selector'], 0)}/{f['blocks']}",
                   choices=sorted({a['config'] for _, _, a in answers}))
        rows.append(agg)
        for (n, s, a), c in zip(answers, checks):
            per_model.setdefault(inst, {}).setdefault(n, []).append(
                {'seed': s, 'config': a['config'], **{k: c[k] for k in ('overstated', 'range_errors', 'unsupported_numbers',
                                                                           'contrary_citations', 'first_half')}})
            if inst != 'main':
                review.append({'instance': inst, 'model': n, 'seed': s, 'config': a['config'],
                               'cited_ids': ' '.join(a['cited_ids']), 'overstated_proxy': c['overstated'],
                               'range_errors': json.dumps(c['range_errors']),
                               'unsupported_numbers': json.dumps(c['unsupported_numbers']), 'explanation': a['explanation']})
        print(inst, {k: agg[k] for k in ('answers', 'invalid', 'selector', 'selector_choice', 'retrieval_citations',
                                          'contrary_citations', 'first_half', 'overstated_explanations',
                                          'explanations_with_range_errors', 'explanations_with_unsupported_numbers',
                                          'selector_block_wins', 'choices')})
    cost = sum(((r.get('meta') or {}).get('usage') or {}).get('cost') or 0 for r in latest.values())
    allcost = sum(((json.loads(x).get('meta') or {}).get('usage') or {}).get('cost') or 0
                  for x in (args.out/'records.jsonl').read_text().splitlines())
    out = {'rows': rows, 'per_model': per_model, 'facts': {n: facts(instance(n)) for n in ['main'] + INSTANCES},
           'reported_cost_usd': round(allcost, 4), 'cost_of_scored_records_usd': round(cost, 4)}
    (args.out/'summary.json').write_text(json.dumps(out, indent=2) + '\n')
    with (args.out/'explanations-for-review.csv').open('w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(review[0]))
        w.writeheader()
        w.writerows(review)
    print('cost', out['reported_cost_usd'])
    if args.tex:
        label = {'main': 'Main (3\\,ms runs)', '4ms': 'I1: 4\\,ms runs', 'relabel': 'I2: labels permuted',
                 'session': 'I3: second session'}
        lines = [r'\begin{tabular}{@{}lrrrrrr@{}}', r'\toprule',
                 r'Evidence & Sel.\ wins & Sel.\ choice & Contrary & First half & Overst. & Range err. \\', r'\midrule']
        for r in rows:
            lines.append(f"{label[r['instance']]} & {r['selector_block_wins']} & {r['selector_choice']}/{r['answers']} & "
                         f"{r['contrary_citations']}/{r['retrieval_citations']} & {r['first_half']}/{r['retrieval_citations']} & "
                         f"{r['overstated_explanations']}/{r['answers']} & {r['explanations_with_range_errors']}/{r['answers']} \\\\")
        lines += [r'\bottomrule', r'\end{tabular}']
        args.tex.write_text('\n'.join(lines) + '\n')
        print(f'wrote {args.tex}')


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run'); r.add_argument('--out', type=Path, required=True)
    r.add_argument('--min-interval', type=float, default=2.0)
    s = sub.add_parser('score'); s.add_argument('--out', type=Path, required=True); s.add_argument('--tex', type=Path)
    a = ap.parse_args()
    {'run': run, 'score': score}[a.cmd](a)


if __name__ == '__main__':
    main()
