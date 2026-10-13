#!/usr/bin/env python3
"""Prompt, order, cap and decoding robustness of the hosted-model audit.

The main audit uses one system prompt, the evidence in its original order, a
six-citation cap and greedy decoding (temperature 0). This study reruns the
full-context prompt of the six hosted models under five conditions, five seeds
each, with the same frozen evidence, schema and OpenRouter settings as
model_audit.py:

* paraphrase  - a reworded system prompt with the same instructions;
* reversed    - retrieval runs presented in reverse order (training table and
                interaction item first, as before), a direct test of whether
                cited runs follow list position or block identity;
* shuffled    - retrieval runs in a seed-specific random order;
* nocap       - the six-citation cap removed from the schema (any number of
                supplied IDs);
* sampled     - temperature 0.7 instead of greedy decoding.

Decisions and citations are scored exactly. Explanations are scored with two
automatic proxies, applied identically to the original runs for comparison:
(a) quantifier overstatement - the explanation attaches "consistently",
"always" or "in all runs" to a comparison ("lowest", "lower", "best"), or says
"significantly" lower, which the evidence does not support (it is lowest in 8 of 10 blocks and no test
is reported); (b) unsupported numbers - decimal numbers in the explanation that
match no evidence value, mean, minimum, maximum or difference at the written
precision. These proxies are not the human-verified claim labels.

    OPENROUTER_API_KEY=... python3 prompt_robustness.py run --out results/prompt-robustness
    python3 prompt_robustness.py score --out results/prompt-robustness [--tex ../../paper/prompt-robustness.tex]
"""
import argparse
import hashlib
import json
import random
import re
import time
from pathlib import Path

import model_audit

HERE = Path(__file__).resolve().parent
RES = HERE/'results'
MODELS = [('Llama-3.3-70B', 'api-llama3.3-70b', 'meta-llama/llama-3.3-70b-instruct'),
          ('Qwen3-235B', 'api-qwen3-235b', 'qwen/qwen3-235b-a22b-2507'),
          ('DeepSeek-V3.2', 'api-deepseek-v3.2', 'deepseek/deepseek-v3.2'),
          ('Nemotron-3-Ultra-550B', 'api-nemotron3-ultra-550b', 'nvidia/nemotron-3-ultra-550b-a55b'),
          ('Gemini-3.8-Flash', 'api-gemini-3.8-flash', 'google/gemini-3.8-flash'),
          ('Gemini-3.1-Pro', 'api-gemini-3.1-pro', 'google/gemini-3.1-pro-preview')]
SEEDS = [4088, 4089, 4090, 4091, 4092]
CONDITIONS = ['paraphrase', 'reversed', 'shuffled', 'nocap', 'sampled']
SELECTOR_CHOICE = 's50000_aall'
PARAPHRASE = ('Your task is to choose, from the allowed configurations, the one that gives the lowest P95 latency '
              'of periodic wake-ups. Answer in JSON with the fields config (one allowed name, spelled exactly), '
              'cited_ids (the IDs of the evidence items you rely on) and explanation. The evidence consists of '
              'measured training summaries and retrieval runs; it contains no held-out test results. Use only the '
              'evidence provided.')
_Q = r'(?:consistently|always|in all (?:the )?(?:retrieval )?runs|across all (?:the )?(?:retrieval )?runs|in every (?:retrieval )?run)'
_C = r'(?:lowest|lower|best|fastest|minimum)'
# A universal quantifier attached to a comparison, or "significantly" + comparative.
OVERSTATE = re.compile(rf'\b{_Q}\b[^.;]{{0,60}}?\b{_C}\b|\b{_C}\b[^.;]{{0,60}}?\b{_Q}\b|'
                       r'\bsignificantly (?:lower|better|faster|higher|less)\b', re.I)


def original_context(d):
    rec = next(r for r in json.loads((RES/f'model-audit-{d}/records.json').read_text())
               if r['variant'] == 'full' and r['status'] == 'valid')
    return json.loads(rec['prompt'])


def build(condition, context, seed):
    """Return (system prompt, evidence list, citation cap, temperature) for one call."""
    ev = context['evidence']
    head = [e for e in ev if e['kind'] != 'retrieval']
    runs = [e for e in ev if e['kind'] == 'retrieval']
    if condition == 'reversed':
        ev = head + runs[::-1]
    elif condition == 'shuffled':
        runs = runs[:]
        random.Random(seed).shuffle(runs)
        ev = head + runs
    system = PARAPHRASE if condition == 'paraphrase' else model_audit.SYSTEM
    cap = len(ev) if condition == 'nocap' else 6
    temperature = 0.7 if condition == 'sampled' else 0
    return system, ev, cap, temperature


def call(model, system, prompt, cap, temperature, seed, key, min_interval, last, opener):
    """One OpenRouter call with the audit's settings; json.dumps(sort_keys) keeps the evidence list order."""
    import urllib.error
    import urllib.request
    context = json.loads(prompt)
    schema = model_audit.answer_schema(context['allowed_configs'], [e['id'] for e in context['evidence']])
    schema['properties']['cited_ids']['maxItems'] = cap
    payload = {'model': model, 'temperature': temperature, 'seed': seed, 'max_tokens': 4096,
               'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': prompt}],
               'response_format': {'type': 'json_schema',
                                   'json_schema': {'name': 'selection', 'strict': True, 'schema': schema}},
               'provider': {'require_parameters': True}}
    attempts = []
    for attempt in range(7):
        time.sleep(max(0.0, last[0] + min_interval - time.monotonic()))
        last[0] = time.monotonic()
        req = urllib.request.Request(model_audit.PROVIDERS['openrouter'][0], data=json.dumps(payload).encode(),
                                     headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key})
        try:
            with opener(req, timeout=300) as resp:
                body = json.load(resp)
            if 'error' in body:
                raise RuntimeError(json.dumps(body['error'])[:300])
            break
        except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError, TimeoutError) as exc:
            code = getattr(exc, 'code', None)
            attempts.append({'status': code, 'error': str(exc)[:300]})
            if code not in (None, 429, 500, 502, 503, 504) or attempt == 6:
                raise RuntimeError(f'failed after {len(attempts)} attempts: {attempts[-1]}')
            time.sleep(min(120, 10 * 2 ** attempt))
    choice = body['choices'][0]
    content = (choice['message'].get('content') or '').strip()
    if content.startswith('```') and content.endswith('```'):
        content = content.split('\n', 1)[1].rsplit('```', 1)[0]
    meta = {'reported_model': body.get('model'), 'response_id': body.get('id'),
            'routed_provider': body.get('provider'), 'finish_reason': choice.get('finish_reason'),
            'usage': body.get('usage'), 'retried_errors': attempts, 'utc_ns': time.time_ns()}
    return content, meta


def run(args):
    import os
    import urllib.request
    key = os.environ.get('OPENROUTER_API_KEY')
    if not key:
        raise SystemExit('OPENROUTER_API_KEY is not set')
    args.out.mkdir(parents=True, exist_ok=True)
    plan = args.out/'plan.json'
    if not plan.exists():  # written before the first call
        plan.write_text(json.dumps({'models': [m for _, _, m in MODELS], 'conditions': CONDITIONS, 'seeds': SEEDS,
                                    'paraphrase_system_prompt': PARAPHRASE, 'sampled_temperature': 0.7,
                                    'max_tokens': 4096, 'response_format': 'strict json_schema',
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
    for name, d, model in MODELS:
        context = original_context(d)
        for condition in CONDITIONS:
            for seed in SEEDS:
                if (name, condition, seed) in done:
                    continue
                system, ev, cap, temp = build(condition, context, seed)
                prompt = json.dumps({'allowed_configs': context['allowed_configs'], 'evidence': ev})
                rec = {'model': name, 'requested_model': model, 'condition': condition, 'seed': seed,
                       'system': system, 'prompt': prompt, 'cap': cap, 'temperature': temp,
                       'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest()}
                try:
                    raw, meta = call(model, system, prompt, cap, temp, seed, key, args.min_interval, last,
                                     urllib.request.urlopen)
                    rec.update(raw=raw, meta=meta)
                    answer = json.loads(raw)
                    model_audit.validate_answer(answer, context['allowed_configs'], ev)
                    if len(answer['cited_ids']) > cap:
                        raise ValueError('citation cap exceeded')
                    rec.update(answer=answer, status='valid')
                except Exception as exc:  # recorded and retried on the next run
                    rec.update(status='invalid', error=str(exc)[:300])
                with path.open('a') as f:
                    f.write(json.dumps(rec) + '\n')
                print(name, condition, seed, rec['status'], rec.get('answer', {}).get('config'), flush=True)


def evidence_numbers(ev):
    vals = [e['p95_us'] for e in ev if e['kind'] == 'retrieval']
    table = [v for e in ev if e['kind'] == 'table' for v in e['values'].values()]
    by_cfg = {}
    for e in ev:
        if e['kind'] == 'retrieval':
            by_cfg.setdefault(e['config'], []).append(e['p95_us'])
    derived = [f(v) for v in by_cfg.values() for f in (min, max, lambda x: sum(x) / len(x))]
    base = vals + table + derived + [e['contrast_us'] for e in ev if e['kind'] == 'graph']
    return base + [abs(a - b) for a in table for b in table]


def unsupported_numbers(text, ev):
    """Decimal numbers that match no evidence-derived value at their written precision."""
    known = evidence_numbers(ev)
    bad = []
    for tok in re.findall(r'(?<![\w.])\d+\.\d+(?![\w.])', text.replace(',', '')):
        prec = len(tok.split('.')[1])
        x = float(tok)
        if not any(abs(round(k, prec) - x) <= 10 ** -prec + 1e-9 for k in known):
            bad.append(tok)
    return bad


def proxies(answer, ev):
    expl = answer.get('explanation', '')
    return {'overstated': bool(OVERSTATE.search(expl)), 'unsupported_numbers': unsupported_numbers(expl, ev)}


def score_set(recs):
    """recs: list of (answer, evidence list in presented order)."""
    n = len(recs)
    sel = sum(a['config'] == SELECTOR_CHOICE for a, _ in recs)
    runs = chosen = first = first_block = 0
    ncites = []
    over = unsup = with_unsup = 0
    for a, ev in recs:
        idx = {e['id']: e for e in ev}
        order = [e['id'] for e in ev if e['kind'] == 'retrieval']
        blocks = sorted({int(x.split('-')[2]) for x in order})
        ncites.append(len(a['cited_ids']))
        for c in a['cited_ids']:
            e = idx.get(c)
            if e is None or e['kind'] != 'retrieval':
                continue
            runs += 1
            chosen += e['config'] == a['config']
            first += order.index(c) < len(order) / 2
            first_block += int(c.split('-')[2]) < blocks[len(blocks) // 2]
        p = proxies(a, ev)
        over += p['overstated']
        unsup += len(p['unsupported_numbers'])
        with_unsup += bool(p['unsupported_numbers'])
    return {'answers': n, 'selector_choice': sel, 'retrieval_citations': runs, 'cited_chosen_config': chosen,
            'cited_first_half_presented': first, 'cited_blocks_0_4': first_block,
            'mean_citations': round(sum(ncites) / n, 2) if n else None,
            'overstated_explanations': over, 'explanations_with_unsupported_numbers': with_unsup,
            'unsupported_numbers': unsup}


def score(args):
    recs = [json.loads(x) for x in (args.out/'records.jsonl').read_text().splitlines()]
    latest = {}
    for r in recs:  # the last attempt per cell counts
        latest[(r['model'], r['condition'], r['seed'])] = r
    valid = [r for r in latest.values() if r['status'] == 'valid']
    rows = {}
    original = []
    for name, d, _ in MODELS:
        for r in json.loads((RES/f'model-audit-{d}/records.json').read_text()):
            if r['variant'] == 'full' and r['status'] == 'valid':
                original.append((r['answer'], json.loads(r['prompt'])['evidence']))
    rows['original'] = score_set(original)
    for c in CONDITIONS:
        rows[c] = score_set([(r['answer'], json.loads(r['prompt'])['evidence']) for r in valid if r['condition'] == c])
    per_model = {name: {c: score_set([(r['answer'], json.loads(r['prompt'])['evidence']) for r in valid
                                      if r['condition'] == c and r['model'] == name]) for c in CONDITIONS}
                 for name, _, _ in MODELS}
    cost = sum((r.get('meta') or {}).get('usage', {}).get('cost') or 0 for r in recs)
    out = {'definition': __doc__.split('Decisions and citations')[1].split('    OPENROUTER')[0].strip(),
           'planned': len(MODELS) * len(CONDITIONS) * len(SEEDS), 'valid': len(valid),
           'invalid_cells': sorted(f'{k[0]}|{k[1]}|{k[2]}' for k, r in latest.items() if r['status'] != 'valid'),
           'calls_including_retries': len(recs), 'reported_cost_usd': round(cost, 4),
           'conditions': rows, 'per_model': per_model}
    (args.out/'summary.json').write_text(json.dumps(out, indent=2) + '\n')
    for c, s in rows.items():
        print(c, s)
    print(f"valid {len(valid)}/{out['planned']}, cost {out['reported_cost_usd']} USD")
    if args.tex:
        names = {'original': 'Original (greedy)', 'paraphrase': 'Paraphrased prompt', 'reversed': 'Reversed runs',
                 'shuffled': 'Shuffled runs', 'nocap': 'No citation cap', 'sampled': 'Sampling ($T{=}0.7$)'}
        lines = [r'\begin{tabular}{@{}lrrrrrr@{}}', r'\toprule',
                 r'Condition & Sel. & Cites & Chosen & First half & Blocks 0--4 & Overst. \\', r'\midrule']
        for c, s in rows.items():
            rc = s['retrieval_citations']
            lines.append(f"{names[c]} & {s['selector_choice']}/{s['answers']} & {s['mean_citations']:.1f} & "
                         f"{s['cited_chosen_config']}/{rc} & {s['cited_first_half_presented']}/{rc} & "
                         f"{s['cited_blocks_0_4']}/{rc} & {s['overstated_explanations']}/{s['answers']} \\\\")
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
