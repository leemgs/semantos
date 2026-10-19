#!/usr/bin/env python3
"""Does internal reasoning change decisions, citations or the checkable errors?

Within-model toggles on the full-context prompt, five seeds each, with the
frozen evidence and output schema of the main audit:

* DeepSeek-V3.2 and Nemotron-3-Ultra-550B ran without reasoning in the main
  audit (zero reasoning tokens); here reasoning is enabled.
* Qwen3-235B-A22B-Instruct-2507 is compared with its thinking variant
  (Qwen3-235B-A22B-Thinking-2507). That endpoint accepts neither a strict JSON
  schema nor a seed, so the schema is stated in the prompt and the answer is
  validated with the same rules; repeated calls replace seeds.
* Gemini 3.8 Flash reasoned by default in the main audit (about 500 reasoning
  tokens per answer); its endpoint does not allow disabling reasoning, so the
  reverse toggle uses the minimal effort setting.
* DeepSeek-V3.2 is pinned to a provider that applies reasoning together with
  the strict schema; Nemotron's only schema-capable provider drops reasoning
  under a strict schema, so Nemotron, like the Qwen3 thinking variant, gets
  the schema in the prompt. An answer counts for an arm that requests
  reasoning only if it spent reasoning tokens.

Answers are scored with the automatic checks of mitigation_baseline.py
(decision, contrary evidence cited, quantifier-overstatement proxy, exact range
check, unsupported numbers), against the same models' original answers. The
recorded usage gives the reasoning tokens actually spent per answer.

    OPENROUTER_API_KEY=... python3 reasoning_models.py run --out results/reasoning-models
    python3 reasoning_models.py score --out results/reasoning-models [--tex ../../paper/reasoning.tex]
"""
import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

import mitigation_baseline as mb
import model_audit
import prompt_robustness as pr

HERE = Path(__file__).resolve().parent
RES = HERE/'results'
# label, original audit directory, requested model, reasoning setting, strict schema, provider routing.
# A first attempt (attempt1-records.jsonl) showed that some providers silently drop reasoning when a strict
# JSON schema is requested (DeepSeek on DeepInfra, Nemotron on its only schema-capable provider), and that
# Gemini 3.8 Flash rejects disabling reasoning; hence the routing and settings below, and the rule that an
# arm requesting reasoning must spend reasoning tokens for an answer to count.
ARMS = [
    ('DeepSeek-V3.2 +reasoning', 'api-deepseek-v3.2', 'deepseek/deepseek-v3.2', {'enabled': True}, True,
     {'order': ['Google'], 'allow_fallbacks': False}),
    ('Nemotron-550B +reasoning', 'api-nemotron3-ultra-550b', 'nvidia/nemotron-3-ultra-550b-a55b', {'enabled': True},
     False, None),
    ('Qwen3-235B thinking', 'api-qwen3-235b', 'qwen/qwen3-235b-a22b-thinking-2507', {'enabled': True}, False, None),
    ('Gemini-3.8-Flash minimal reasoning', 'api-gemini-3.8-flash', 'google/gemini-3.8-flash', {'effort': 'minimal'},
     True, None),
]
ORIGINAL_NAME = {'api-deepseek-v3.2': 'DeepSeek-V3.2', 'api-nemotron3-ultra-550b': 'Nemotron-3-Ultra-550B',
                 'api-qwen3-235b': 'Qwen3-235B', 'api-gemini-3.8-flash': 'Gemini-3.8-Flash'}
SCHEMA_NOTE = (' Respond with only a JSON object with the keys "config" (one of the allowed names), "cited_ids" (a list '
               'of at most six evidence IDs from the prompt) and "explanation" (at most 400 characters).')


def call(model, system, prompt, reasoning, strict, seed, key, last, provider=None, min_interval=2.0):
    context = json.loads(prompt)
    payload = {'model': model, 'temperature': 0, 'max_tokens': 16000, 'reasoning': reasoning,
               'messages': [{'role': 'system', 'content': system + ('' if strict else SCHEMA_NOTE)},
                            {'role': 'user', 'content': prompt}]}
    if not strict and provider:
        payload['provider'] = provider
    if strict:
        schema = model_audit.answer_schema(context['allowed_configs'], [e['id'] for e in context['evidence']])
        payload.update(seed=seed, provider={'require_parameters': True, **(provider or {})},
                       response_format={'type': 'json_schema',
                                        'json_schema': {'name': 'selection', 'strict': True, 'schema': schema}})
    attempts = []
    for attempt in range(7):
        time.sleep(max(0.0, last[0] + min_interval - time.monotonic()))
        last[0] = time.monotonic()
        req = urllib.request.Request(model_audit.PROVIDERS['openrouter'][0], data=json.dumps(payload).encode(),
                                     headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key})
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
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
    if content.startswith('```'):
        content = content.split('\n', 1)[1].rsplit('```', 1)[0]
    start, end = content.find('{'), content.rfind('}')
    if not strict and start >= 0:
        content = content[start:end + 1]
    usage = body.get('usage') or {}
    meta = {'reported_model': body.get('model'), 'response_id': body.get('id'), 'routed_provider': body.get('provider'),
            'finish_reason': choice.get('finish_reason'), 'usage': usage,
            'reasoning_tokens': (usage.get('completion_tokens_details') or {}).get('reasoning_tokens'),
            'retried_errors': attempts, 'utc_ns': time.time_ns()}
    return content, meta


def run(args):
    import os
    key = os.environ.get('OPENROUTER_API_KEY')
    if not key:
        raise SystemExit('OPENROUTER_API_KEY is not set')
    args.out.mkdir(parents=True, exist_ok=True)
    plan = args.out/'plan.json'
    if not plan.exists():
        plan.write_text(json.dumps({'arms': [{'label': a, 'original': d, 'model': m, 'reasoning': r, 'strict_schema': s,
                                              'provider': p} for a, d, m, r, s, p in ARMS],
                                    'seeds': pr.SEEDS, 'temperature': 0,
                                    'max_tokens': 16000, 'schema_note_when_not_strict': SCHEMA_NOTE,
                                    'rule': 'an arm requesting reasoning counts an answer only if reasoning tokens > 0',
                                    'key_env': 'OPENROUTER_API_KEY',
                                    'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                    'started_utc_ns': time.time_ns()}, indent=2) + '\n')
    path = args.out/'records.jsonl'
    done = set()
    if path.exists():
        for line in path.read_text().splitlines():
            r = json.loads(line)
            if r['status'] == 'valid':
                done.add((r['arm'], r['seed']))
    last = [0.0]
    for arm, d, model, reasoning, strict, provider in ARMS:
        context = pr.original_context(d)
        prompt = json.dumps({'allowed_configs': context['allowed_configs'], 'evidence': context['evidence']})
        for seed in pr.SEEDS:
            if (arm, seed) in done:
                continue
            rec = {'arm': arm, 'requested_model': model, 'reasoning': reasoning, 'strict_schema': strict, 'seed': seed,
                   'system': model_audit.SYSTEM, 'prompt': prompt,
                   'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest()}
            try:
                raw, meta = call(model, model_audit.SYSTEM, prompt, reasoning, strict, seed, key, last, provider)
                rec.update(raw=raw, meta=meta)
                if reasoning.get('enabled') and not meta.get('reasoning_tokens'):
                    raise ValueError(f"reasoning requested but not applied by {meta.get('routed_provider')}")
                answer = json.loads(raw)
                model_audit.validate_answer(answer, context['allowed_configs'], context['evidence'])
                if len(answer['cited_ids']) > 6:
                    raise ValueError('citation cap exceeded')
                rec.update(answer=answer, status='valid')
            except Exception as exc:
                rec.update(status='invalid', error=str(exc)[:300])
            with path.open('a') as f:
                f.write(json.dumps(rec) + '\n')
            print(arm, seed, rec['status'], rec.get('answer', {}).get('config'),
                  'reasoning_tokens', (rec.get('meta') or {}).get('reasoning_tokens'), flush=True)


def score(args):
    recs = [json.loads(x) for x in (args.out/'records.jsonl').read_text().splitlines()]
    latest = {}
    for r in recs:
        latest[(r['arm'], r['seed'])] = r
    orig = mb.original_answers()
    rows = []
    for arm, d, model, reasoning, strict, provider in ARMS:
        name = ORIGINAL_NAME[d]
        base = [(a, ev) for m, _, a, ev in orig if m == name]
        new = [r for (a, _), r in latest.items() if a == arm and r['status'] == 'valid']
        ev = pr.original_context(d)['evidence']
        orig_rt = [((r.get('response_meta') or {}).get('usage') or {}).get('completion_tokens_details', {}).get('reasoning_tokens')
                   for r in json.loads((RES/f'model-audit-{d}/records.json').read_text())
                   if r['variant'] == 'full' and r.get('status') == 'valid']
        new_rt = [r['meta'].get('reasoning_tokens') for r in new]
        rows.append({'arm': arm, 'model': model, 'reasoning': reasoning, 'strict_schema': strict,
                     'original': mb.aggregate([mb.check(a, e) for a, e in base]),
                     'toggled': mb.aggregate([mb.check(r['answer'], ev) for r in new]),
                     'original_reasoning_tokens': orig_rt, 'toggled_reasoning_tokens': new_rt,
                     'invalid_cells': [s for (a, s), r in latest.items() if a == arm and r['status'] != 'valid']})
    cost = sum((r.get('meta') or {}).get('usage', {}).get('cost') or 0 for r in recs)
    out = {'arms': rows, 'calls_including_retries': len(recs), 'reported_cost_usd': round(cost, 4)}
    (args.out/'summary.json').write_text(json.dumps(out, indent=2) + '\n')
    for r in rows:
        o, t = r['original'], r['toggled']
        print(f"{r['arm']}: answers {t['answers']}, reasoning tokens {r['original_reasoning_tokens']} -> {r['toggled_reasoning_tokens']}")
        for k in ('selector_choice', 'contrary_evidence', 'overstated_explanations', 'explanations_with_range_errors',
                  'explanations_with_unsupported_numbers', 'mean_chars'):
            print(f'   {k}: {o[k]} -> {t[k]}')
    print(f"cost {out['reported_cost_usd']} USD")
    if args.tex:
        lines = [r'\begin{tabular}{@{}lrrrrr@{}}', r'\toprule',
                 r'Model (toggle) & Reas.\ tok. & Sel. & Contrary & Overst. & Range err. \\', r'\midrule']
        short = {'DeepSeek-V3.2 +reasoning': 'DeepSeek-V3.2 (on)', 'Nemotron-550B +reasoning': 'Nemotron-550B (on)',
                 'Qwen3-235B thinking': 'Qwen3-235B (thinking)', 'Gemini-3.8-Flash minimal reasoning': 'Gemini-Flash (minimal)'}
        for r in rows:
            o, t = r['original'], r['toggled']
            mean = lambda v: round(sum(x or 0 for x in v) / len(v)) if v else 0
            lines.append(f"{short[r['arm']]} & {mean(r['original_reasoning_tokens'])}$\\to${mean(r['toggled_reasoning_tokens'])} & "
                         f"{o['selector_choice']}$\\to${t['selector_choice']}/{t['answers']} & "
                         f"{o['contrary_evidence']}$\\to${t['contrary_evidence']} & "
                         f"{o['overstated_explanations']}$\\to${t['overstated_explanations']} & "
                         f"{o['explanations_with_range_errors']}$\\to${t['explanations_with_range_errors']} \\\\")
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
