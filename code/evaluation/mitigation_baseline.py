#!/usr/bin/env python3
"""Do simple mitigations reduce misstated explanations?

Reruns the full-context prompt of the six hosted models (five seeds) with the
frozen evidence, schema and OpenRouter settings of the main audit, under three
mitigations:

* verify       - the system prompt adds an explicit instruction to check every
                 number, range, extreme and comparison against the evidence, to
                 avoid quantifiers the evidence does not support, and to cite
                 evidence against the choice as well as for it;
* stats        - the evidence list gains one deterministic "summary" item per
                 configuration (minimum, maximum and mean of its retrieval runs
                 and the number of blocks in which it is lowest), a tool-style
                 aid that removes the need to aggregate by hand;
* verify+stats - both.

Explanations of these new answers have no human-verified claim labels, so they
are scored with automatic checks applied identically to the original runs:
decision (selector's choice or not), cited retrieval runs or summary items of a
competing configuration, the quantifier-overstatement proxy of prompt_robustness.py, an
exact range check (a stated range for a configuration must equal the minimum
and maximum of its runs, or of the runs the answer cites, at the written
precision), and unsupported decimal numbers. `validate` reports how the range
check and the overstatement proxy compare with the human-verified labels on
the original runs.

    OPENROUTER_API_KEY=... python3 mitigation_baseline.py run --out results/mitigation-baseline
    python3 mitigation_baseline.py validate
    python3 mitigation_baseline.py score --out results/mitigation-baseline [--tex ../../paper/mitigation.tex]
"""
import argparse
import hashlib
import json
import re
import time
import urllib.request
from pathlib import Path

import model_audit
import prompt_robustness as pr

HERE = Path(__file__).resolve().parent
RES = HERE/'results'
CONDITIONS = ['verify', 'stats', 'verify+stats']
VERIFY = (' Before writing the explanation, check every number, range, minimum, maximum and comparison you state '
          'against the evidence items, and state only what the evidence supports: do not say "consistently", '
          '"always", "in all runs" or "significantly" unless every relevant item supports it. Cite evidence that '
          'favors other configurations as well as evidence that favors your choice.')
CONFIGS = ['s50000_aall', 's50000_aone', 's1000000_aall', 's1000000_aone']


def summary_items(ev):
    runs = [e for e in ev if e['kind'] == 'retrieval']
    by_block = {}
    for e in runs:
        by_block.setdefault(int(e['id'].split('-')[2]), []).append(e)
    lowest = {c: 0 for c in CONFIGS}
    for items in by_block.values():
        lowest[min(items, key=lambda e: e['p95_us'])['config']] += 1
    out = []
    for c in CONFIGS:
        v = [e['p95_us'] for e in runs if e['config'] == c]
        out.append({'id': f'summary-{c}', 'kind': 'summary', 'config': c, 'retrieval_runs': len(v),
                    'min_p95_us': round(min(v), 3), 'max_p95_us': round(max(v), 3),
                    'mean_p95_us': round(sum(v) / len(v), 3), 'blocks_where_lowest': lowest[c],
                    'blocks': len(by_block)})
    return out


def build(condition, context):
    ev = list(context['evidence'])
    if 'stats' in condition:
        ev = ev + summary_items(ev)
    system = model_audit.SYSTEM + (VERIFY if 'verify' in condition else '')
    return system, ev


# --- exact range check -------------------------------------------------------------------------------------
NUM = r'~?\s*(\d+(?:\.\d+)?)'
RANGE = re.compile(rf'(?:from|between|range\w*(?:\s+from)?|\()\s*{NUM}\s*(?:µs|μs|us|microseconds)?\s*(?:to|-|–|—|and)\s*{NUM}', re.I)
CFG = re.compile(r's(?:50000|1000000)_a(?:all|one)|(?:both\s+)?s1000000(?:\s+(?:configs?|configurations?))', re.I)


def _matches(x, target, approx):
    if approx:
        return abs(x - target) <= 1.0
    prec = len(str(x).split('.')[1]) if '.' in str(x) else 0
    return abs(round(target, prec) - x) <= 10 ** -prec + 1e-9


def range_errors(text, ev, cited):
    """Stated ranges that match neither all runs nor the cited runs of the configuration they describe."""
    runs = [e for e in ev if e['kind'] == 'retrieval']
    errors = []
    for sent in re.split(r'(?<=[.;])\s+', text):
        for m in RANGE.finditer(sent):
            before = list(CFG.finditer(sent[:m.start()]))
            if not before:
                continue
            name = before[-1].group(0).lower()
            cfgs = [c for c in CONFIGS if c.startswith('s1000000')] if '_' not in name else [name]
            a, b = float(m.group(1)), float(m.group(2))
            approx = '~' in m.group(0)
            ok = False
            for subset in ([e for e in runs if e['config'] in cfgs],
                           [e for e in runs if e['config'] in cfgs and e['id'] in cited]):
                v = [e['p95_us'] for e in subset]
                if v and _matches(a, min(v), approx) and _matches(b, max(v), approx):
                    ok = True
            if not ok:
                errors.append(f'{name}: {m.group(1)}-{m.group(2)}')
    return errors


def check(answer, ev):
    idx = {e['id']: e for e in ev}
    cited = answer['cited_ids']
    runs = [idx[c] for c in cited if c in idx and idx[c]['kind'] == 'retrieval']
    expl = answer['explanation']
    items = [idx[c] for c in cited if c in idx and idx[c]['kind'] in ('retrieval', 'summary')]
    return {'selector_choice': answer['config'] == 's50000_aall',
            'retrieval_citations': len(runs), 'contrary_citations': sum(e['config'] != answer['config'] for e in runs),
            'evidence_citations': len(items), 'contrary_evidence': sum(e['config'] != answer['config'] for e in items),
            'cites_summary': any(c.startswith('summary-') for c in cited),
            'overstated': bool(pr.OVERSTATE.search(expl)), 'range_errors': range_errors(expl, ev, set(cited)),
            'unsupported_numbers': pr.unsupported_numbers(expl, ev), 'chars': len(expl)}


def aggregate(checks):
    n = len(checks)
    return {'answers': n, 'selector_choice': sum(c['selector_choice'] for c in checks),
            'retrieval_citations': sum(c['retrieval_citations'] for c in checks),
            'contrary_citations': sum(c['contrary_citations'] for c in checks),
            'answers_citing_contrary': sum(c['contrary_citations'] > 0 for c in checks),
            'evidence_citations': sum(c['evidence_citations'] for c in checks),
            'contrary_evidence': sum(c['contrary_evidence'] for c in checks),
            'answers_citing_contrary_evidence': sum(c['contrary_evidence'] > 0 for c in checks),
            'answers_citing_summary': sum(c['cites_summary'] for c in checks),
            'overstated_explanations': sum(c['overstated'] for c in checks),
            'explanations_with_range_errors': sum(bool(c['range_errors']) for c in checks),
            'explanations_with_unsupported_numbers': sum(bool(c['unsupported_numbers']) for c in checks),
            'mean_chars': round(sum(c['chars'] for c in checks) / n) if n else None}


def original_answers():
    out = []
    for name, d, _ in pr.MODELS:
        for r in json.loads((RES/f'model-audit-{d}/records.json').read_text()):
            if r['variant'] == 'full' and r['status'] == 'valid':
                out.append((name, r['seed'], r['answer'], json.loads(r['prompt'])['evidence']))
    return out


def validate(args):
    """Compare the automatic checks with the human-verified labels of the original hosted explanations."""
    audit = json.loads((RES/'model-audit-summary/claim-audit.json').read_text())['claims']
    rows = []
    for name, seed, ans, ev in original_answers():
        c = check(ans, ev)
        rows.append({'model': name, 'seed': seed, 'range_errors': c['range_errors'], 'overstated_proxy': c['overstated']})
    flagged = [r for r in rows if r['range_errors']]
    for r in flagged:
        print('range check flags', r['model'], r['seed'], r['range_errors'])
    wrong_ranges = [x for x in audit if x['model'] in {m for m, _, _ in pr.MODELS} and x['verdict'] == 'wrong'
                    and re.search(r'range', x['claim'])]
    print(f'{len(flagged)} of {len(rows)} original explanations flagged by the range check; verified wrong range '
          f'claims: {len(wrong_ranges)} ({", ".join(sorted({x["model"] for x in wrong_ranges}))})')
    over_models = {x['model'] for x in audit if x['verdict'] == 'overstated' and x['model'] in {m for m, _, _ in pr.MODELS}}
    proxy_models = {r['model'] for r in rows if r['overstated_proxy']}
    print(f'overstatement proxy fires in {sum(r["overstated_proxy"] for r in rows)}/{len(rows)} explanations; '
          f'models with verified overstatements: {sorted(over_models)}; models flagged by the proxy: {sorted(proxy_models)}')
    return rows


def run(args):
    import os
    key = os.environ.get('OPENROUTER_API_KEY')
    if not key:
        raise SystemExit('OPENROUTER_API_KEY is not set')
    args.out.mkdir(parents=True, exist_ok=True)
    plan = args.out/'plan.json'
    if not plan.exists():
        plan.write_text(json.dumps({'models': [m for _, _, m in pr.MODELS], 'conditions': CONDITIONS, 'seeds': pr.SEEDS,
                                    'verify_instruction': VERIFY, 'temperature': 0, 'max_tokens': 4096,
                                    'response_format': 'strict json_schema', 'citation_cap': 6,
                                    'provider_require_parameters': True, 'key_env': 'OPENROUTER_API_KEY',
                                    'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                    'started_utc_ns': time.time_ns()}, indent=2) + '\n')
    path = args.out/'records.jsonl'
    done = set()
    if path.exists():
        for line in path.read_text().splitlines():
            r = json.loads(line)
            if r['status'] == 'valid':
                done.add((r['model'], r['condition'], r['seed']))
    last = [0.0]
    for name, d, model in pr.MODELS:
        context = pr.original_context(d)
        for condition in CONDITIONS:
            for seed in pr.SEEDS:
                if (name, condition, seed) in done:
                    continue
                system, ev = build(condition, context)
                prompt = json.dumps({'allowed_configs': context['allowed_configs'], 'evidence': ev})
                rec = {'model': name, 'requested_model': model, 'condition': condition, 'seed': seed,
                       'system': system, 'prompt': prompt, 'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest()}
                try:
                    raw, meta = pr.call(model, system, prompt, 6, 0, seed, key, args.min_interval, last,
                                        urllib.request.urlopen)
                    rec.update(raw=raw, meta=meta)
                    answer = json.loads(raw)
                    model_audit.validate_answer(answer, context['allowed_configs'], ev)
                    if len(answer['cited_ids']) > 6:
                        raise ValueError('citation cap exceeded')
                    rec.update(answer=answer, status='valid')
                except Exception as exc:  # recorded; retried on the next run
                    rec.update(status='invalid', error=str(exc)[:300])
                with path.open('a') as f:
                    f.write(json.dumps(rec) + '\n')
                print(name, condition, seed, rec['status'], rec.get('answer', {}).get('config'), flush=True)


def score(args):
    recs = [json.loads(x) for x in (args.out/'records.jsonl').read_text().splitlines()]
    latest = {}
    for r in recs:
        latest[(r['model'], r['condition'], r['seed'])] = r
    valid = [r for r in latest.values() if r['status'] == 'valid']
    rows = {'original': aggregate([check(a, ev) for _, _, a, ev in original_answers()])}
    per_model = {}
    for c in CONDITIONS:
        sel = [r for r in valid if r['condition'] == c]
        rows[c] = aggregate([check(r['answer'], json.loads(r['prompt'])['evidence']) for r in sel])
    for name, _, _ in pr.MODELS:
        per_model[name] = {'original': aggregate([check(a, ev) for m, _, a, ev in original_answers() if m == name])}
        for c in CONDITIONS:
            per_model[name][c] = aggregate([check(r['answer'], json.loads(r['prompt'])['evidence'])
                                            for r in valid if r['condition'] == c and r['model'] == name])
    cost = sum((r.get('meta') or {}).get('usage', {}).get('cost') or 0 for r in recs)
    out = {'planned': len(pr.MODELS) * len(CONDITIONS) * len(pr.SEEDS), 'valid': len(valid),
           'invalid_cells': sorted(f'{k[0]}|{k[1]}|{k[2]}' for k, r in latest.items() if r['status'] != 'valid'),
           'calls_including_retries': len(recs), 'reported_cost_usd': round(cost, 4),
           'conditions': rows, 'per_model': per_model,
           'flagged': [{'model': r['model'], 'condition': r['condition'], 'seed': r['seed'],
                        **{k: v for k, v in check(r['answer'], json.loads(r['prompt'])['evidence']).items()
                           if k in ('range_errors', 'unsupported_numbers', 'overstated')}}
                       for r in valid]}
    (args.out/'summary.json').write_text(json.dumps(out, indent=2) + '\n')
    for c, s in rows.items():
        print(c, s)
    print(f"valid {len(valid)}/{out['planned']}, cost {out['reported_cost_usd']} USD")
    if args.tex:
        names = {'original': 'Original prompt', 'verify': 'Verify instruction', 'stats': 'Summary statistics',
                 'verify+stats': 'Both'}
        lines = [r'\begin{tabular}{@{}lrrrrr@{}}', r'\toprule',
                 r'Condition & Sel. & Contrary cites & Overst. & Range err. & Unsupp. num. \\', r'\midrule']
        # contrary cites: cited runs or summaries of a configuration other than the chosen one
        for c, s in rows.items():
            lines.append(f"{names[c]} & {s['selector_choice']}/{s['answers']} & "
                         f"{s['contrary_evidence']}/{s['evidence_citations']} & {s['overstated_explanations']}/{s['answers']} & "
                         f"{s['explanations_with_range_errors']}/{s['answers']} & "
                         f"{s['explanations_with_unsupported_numbers']}/{s['answers']} \\\\")
        lines += [r'\bottomrule', r'\end{tabular}']
        args.tex.write_text('\n'.join(lines) + '\n')
        print(f'wrote {args.tex}')


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run'); r.add_argument('--out', type=Path, required=True)
    r.add_argument('--min-interval', type=float, default=2.0)
    sub.add_parser('validate')
    s = sub.add_parser('score'); s.add_argument('--out', type=Path, required=True); s.add_argument('--tex', type=Path)
    a = ap.parse_args()
    {'run': run, 'validate': validate, 'score': score}[a.cmd](a)


if __name__ == '__main__':
    main()
