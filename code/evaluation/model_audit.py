"""Run matched-context model ablations and context-deletion interventions.

Uses only train/retrieval inputs from a controlled-kernel artifact. No model result
is inferred from a failed backend, and test outcomes are never sent to the model.
This narrow configuration-selection task is not the REST VM-sysctl deployment.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import statistics
import time
import urllib.error
import urllib.request

from controlled_kernel import digest, quantile, write

SYSTEM = ('Select one allowed config to minimize periodic wake-up P95 latency. '
          'Return JSON with config (exact allowed name), cited_ids (evidence IDs), '
          'and explanation. Evidence contains measured training summaries and '
          'retrieval runs, not held-out test outcomes. Do not invent evidence.')


def evidence(root):
    frozen = json.loads((root/'frozen.json').read_text())
    plan = json.loads((root/'plan.json').read_text())
    rows = [json.loads(line) for line in (root/'runs.jsonl').read_text().splitlines()]
    items = [{'id': 'training-table', 'kind': 'table', 'values': frozen['means_p95_us']},
             {'id': 'interaction', 'kind': 'graph', 'contrast_us': frozen['interaction_us'],
              'edges': frozen['edges'], 'scope': frozen['scope']}]
    items.extend({'id': r['id'], 'kind': 'retrieval', 'config': r['name'],
                  'period_ns': r['period_ns'], 'p95_us': quantile(r['events'])}
                 for r in rows if r['role'] == 'retrieval')
    return plan, items


def validate_answer(answer, allowed, items):
    if not isinstance(answer, dict) or answer.get('config') not in allowed:
        raise ValueError('invalid config')
    cites = answer.get('cited_ids')
    if not isinstance(cites, list) or not all(isinstance(i, str) for i in cites):
        raise ValueError('cited_ids must be strings')
    if set(cites) - {e['id'] for e in items}:
        raise ValueError('invented or deleted evidence citation')
    if not isinstance(answer.get('explanation'), str):
        raise ValueError('explanation required')
    return answer


def experiment(root, backend, seeds):
    plan, items = evidence(root)
    allowed = [c['name'] for c in plan['configs']]
    records = []

    def invoke(variant, context, seed):
        prompt = json.dumps({'allowed_configs': allowed, 'evidence': context}, sort_keys=True)
        started = time.monotonic()
        record = {'variant': variant, 'seed': seed, 'prompt': prompt, 'system': SYSTEM,
                  'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                  'input_evidence_ids': [i['id'] for i in context]}
        try:
            raw = backend(SYSTEM, prompt, seed)
            if isinstance(raw, dict):  # API backends also return provider metadata
                record['response_meta'] = raw['meta']
                raw = raw['content']
            record['raw_response'] = raw
            answer = json.loads(raw)
            record['answer'] = validate_answer(answer, allowed, context)
            record['status'] = 'valid'
        except Exception as exc:
            record.update(status='failed', error_type=type(exc).__name__, error=str(exc))
        record['elapsed_seconds'] = time.monotonic()-started
        records.append(record)
        return record

    for seed in seeds:
        full = invoke('full', items, seed)
        if full['status'] != 'valid':
            # Do not spend repeated calls on an unavailable endpoint.
            break
        for variant, removed in [('no_graph', {'graph'}), ('no_retrieval', {'retrieval'}),
                                 ('model_only', {'table', 'graph', 'retrieval'})]:
            invoke(variant, [i for i in items if i['kind'] not in removed], seed)
        cited = set(full['answer']['cited_ids'])
        cited_items = [i for i in items if i['id'] in cited]
        uncited = [i for i in items if i['id'] not in cited]
        # Matched kind and count, without reusing controls; otherwise mark unavailable.
        controls = []
        for item in cited_items:
            control = next((i for i in uncited if i['kind'] == item['kind'] and i not in controls), None)
            if control is None:
                controls = None
                break
            controls.append(control)
        if not cited_items or controls is None:
            records.append({'variant': 'faithfulness', 'seed': seed, 'status': 'not_estimable',
                            'reason': 'no citations or no same-kind uncited controls'})
        else:
            deleted = invoke('delete_cited', [i for i in items if i['id'] not in cited], seed)
            control_ids = {i['id'] for i in controls}
            placebo = invoke('delete_uncited', [i for i in items if i['id'] not in control_ids], seed)
            if deleted['status'] == placebo['status'] == 'valid':
                records.append({'variant': 'faithfulness', 'seed': seed, 'status': 'valid',
                                'cited_deleted': sorted(cited), 'uncited_deleted': sorted(control_ids),
                                'cited_action_changed': deleted['answer']['config'] != full['answer']['config'],
                                'uncited_action_changed': placebo['answer']['config'] != full['answer']['config']})
    return records


def heldout(root, records):
    """Score each valid choice by paired offline replay on the frozen test grid.

    Uses exactly the rule of analyze_controlled.py for the non-LLM selectors: the
    chosen configuration's per-block run P95, and the paired reduction against the
    explicit control (the first planned configuration) within each block. Test
    outcomes are read only here, after every model call has finished.
    """
    plan = json.loads((root/'plan.json').read_text())
    rows = [json.loads(line) for line in (root/'runs.jsonl').read_text().splitlines()]
    control = plan['configs'][0]['name']
    t = 2.2621571628540993  # Student-t 0.975 quantile, 9 degrees of freedom (ten blocks)

    def interval(values):
        return {'mean': statistics.mean(values), 'ci95_halfwidth': t*statistics.stdev(values)/len(values)**.5}

    table = {}
    for ms in plan['roles_ms']['test']:
        lookup = {(r['block'], r['name']): r for r in rows if r['role'] == 'test' and r['period_ns'] == ms*1000000}
        for name in (c['name'] for c in plan['configs']):
            picked = [lookup[b, name] for b in range(plan['blocks'])]
            base = [lookup[b, control] for b in range(plan['blocks'])]
            table[ms, name] = {'p95_us': interval([quantile(r['events']) for r in picked]),
                               'reduction_pct': interval([100*(1-quantile(r['events'])/quantile(c['events']))
                                                          for r, c in zip(picked, base)])}
    scored = []
    for r in records:
        if r.get('status') != 'valid' or 'answer' not in r:
            continue
        name = r['answer']['config']
        for ms in plan['roles_ms']['test']:
            scored.append({'variant': r['variant'], 'seed': r['seed'], 'period_ms': ms, 'config': name,
                           'same_as_control': name == control, **table[ms, name],
                           'scope': 'paired offline replay on held-out grid, same rule as the non-LLM selectors'})
    return scored


def answer_schema(allowed, ids):
    cite = {'type': 'string', 'enum': ids} if ids else {'type': 'string'}
    return {'type': 'object', 'required': ['config', 'cited_ids', 'explanation'],
            'properties': {'config': {'type': 'string', 'enum': allowed},
                           'cited_ids': {'type': 'array', 'items': cite, 'maxItems': 6 if ids else 0},
                           'explanation': {'type': 'string', 'maxLength': 400}}}


# OpenAI-compatible chat-completions endpoints and the environment variable holding
# each key. Keys are read from the environment only and never written to disk.
PROVIDERS = {
    'openrouter': ('https://openrouter.ai/api/v1/chat/completions', 'OPENROUTER_API_KEY'),
    'gemini': ('https://generativelanguage.googleapis.com/v1beta/openai/chat/completions', 'GEMINI_API_KEY'),
    'openai': ('https://api.openai.com/v1/chat/completions', 'CHATGPT_API_KEY'),
}


def api_backend(provider, model, response_format='json_schema', max_tokens=1024,
                min_interval=6.0, retries=6, opener=urllib.request.urlopen):
    """Hosted model via an OpenAI-compatible API.

    Unlike local GGUF runs, hosted weights cannot be hashed and providers may change
    or route a model silently; each call therefore records the provider's reported
    model, response id, fingerprint and routing. `json_schema` sends the same schema
    as the local grammar (OpenRouter is told to use only providers that honor it);
    `json_object` and `none` rely on the prompt, and answers are re-validated either way.
    """
    url, key_env = PROVIDERS[provider]
    key = os.environ.get(key_env)
    if not key:
        raise SystemExit(f'{key_env} is not set')
    last = [0.0]

    def backend(system, prompt, seed):
        context = json.loads(prompt)
        payload = {'model': model, 'temperature': 0, 'seed': seed, 'max_tokens': max_tokens,
                   'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': prompt}]}
        if response_format == 'json_schema':
            schema = answer_schema(context['allowed_configs'], [e['id'] for e in context['evidence']])
            payload['response_format'] = {'type': 'json_schema',
                                          'json_schema': {'name': 'selection', 'strict': True, 'schema': schema}}
        elif response_format == 'json_object':
            payload['response_format'] = {'type': 'json_object'}
        if provider == 'openrouter':
            payload['provider'] = {'require_parameters': response_format != 'none'}
        attempts = []
        for attempt in range(retries+1):
            time.sleep(max(0.0, last[0]+min_interval-time.monotonic()))
            last[0] = time.monotonic()
            request = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                             headers={'Content-Type': 'application/json',
                                                      'Authorization': 'Bearer '+key})
            try:
                with opener(request, timeout=300) as response:
                    body = json.load(response)
                break
            except urllib.error.HTTPError as exc:
                attempts.append({'status': exc.code, 'body': exc.read()[:300].decode('utf-8', 'replace')})
                if exc.code not in (429, 500, 502, 503, 504) or attempt == retries:
                    raise RuntimeError(f'HTTP {exc.code} after {len(attempts)} attempts: {attempts[-1]["body"]}')
                time.sleep(min(120, 10*2**attempt))
        if 'error' in body:
            raise RuntimeError(f"provider error: {json.dumps(body['error'])[:300]}")
        choice = body['choices'][0]
        content = choice['message'].get('content') or ''
        stripped = content.strip()
        fenced = stripped.startswith('```') and stripped.endswith('```')
        if fenced:  # a single surrounding Markdown fence is removed and recorded
            stripped = stripped.split('\n', 1)[1].rsplit('```', 1)[0]
        meta = {'reported_model': body.get('model'), 'response_id': body.get('id'),
                'system_fingerprint': body.get('system_fingerprint'), 'routed_provider': body.get('provider'),
                'finish_reason': choice.get('finish_reason'), 'usage': body.get('usage'),
                'fence_stripped': fenced, 'retried_errors': attempts, 'utc_ns': time.time_ns()}
        return {'content': stripped, 'meta': meta}

    manifest = {'format': 'hosted API (weights not hashable)', 'provider': provider, 'endpoint': url,
                'requested_model': model, 'response_format': response_format, 'max_tokens': max_tokens,
                'temperature': 0, 'min_interval_seconds': min_interval, 'key_env': key_env,
                'sha256': None}
    return backend, manifest


def llamacpp_backend(path, n_ctx, threads):
    from llama_cpp import Llama, __version__ as llama_cpp_version
    model = Llama(model_path=str(path), n_ctx=n_ctx, n_threads=threads, verbose=False)
    meta = {k: v for k, v in model.metadata.items() if k.startswith('general.')}

    def backend(system, prompt, seed):
        # Constrained decoding: the grammar fixes the answer's shape and restricts
        # `config` to the allowed names and citations to the supplied evidence IDs
        # (still re-checked afterwards). Model-only prompts carry no evidence to cite.
        context = json.loads(prompt)
        schema = answer_schema(context['allowed_configs'], [e['id'] for e in context['evidence']])
        model.set_seed(seed)
        out = model.create_chat_completion(
            messages=[{'role': 'system', 'content': system}, {'role': 'user', 'content': prompt}],
            temperature=0, seed=seed, max_tokens=384,
            response_format={'type': 'json_object', 'schema': schema})
        return out['choices'][0]['message']['content']

    # llama.cpp loads split GGUFs (name-00001-of-0000N.gguf) from the first shard;
    # hash every shard so the recorded weights are complete.
    shards = [path]
    if '-00001-of-' in path.name:
        count = int(path.stem.rsplit('-of-', 1)[1])
        shards = [path.with_name(path.name.replace('-00001-of-', f'-{i:05d}-of-')) for i in range(1, count+1)]
    manifest = {'format': 'gguf', 'file': path.name, 'bytes': sum(s.stat().st_size for s in shards),
                'sha256': digest(path), 'gguf_general_metadata': meta,
                'shards': [{'file': s.name, 'bytes': s.stat().st_size, 'sha256': digest(s)} for s in shards],
                'runtime': 'llama-cpp-python ' + llama_cpp_version, 'n_ctx': n_ctx,
                'response_format': 'JSON schema grammar: config enum; <=6 citations restricted to supplied IDs; <=400-char explanation', 'max_tokens': 384}
    return backend, manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--backend', choices=['ollama', 'llamacpp', 'api'], default='ollama')
    p.add_argument('--model', required=True, help='model name recorded in plan.json')
    p.add_argument('--manifest', type=Path, help='ollama: local manifest for the exact installed model')
    p.add_argument('--endpoint', default='http://127.0.0.1:11434')
    p.add_argument('--gguf', type=Path, help='llamacpp: path to the GGUF weights (hashed into the plan)')
    p.add_argument('--n-ctx', type=int, default=8192)
    p.add_argument('--threads', type=int, default=4)
    p.add_argument('--provider', choices=sorted(PROVIDERS), help='api: hosted provider')
    p.add_argument('--response-format', default='json_schema', choices=['json_schema', 'json_object', 'none'])
    p.add_argument('--max-tokens', type=int, default=1024, help='api: completion token limit')
    p.add_argument('--min-interval', type=float, default=6.0, help='api: seconds between requests')
    p.add_argument('--purpose', default='experiment', choices=['experiment', 'pipeline-check'],
                   help='pipeline-check runs are plumbing tests and must not be reported as results')
    args = p.parse_args()
    if args.out.exists():
        p.error('choose a new output directory')
    if args.backend == 'ollama' and not args.manifest:
        p.error('--manifest is required for the ollama backend')
    if args.backend == 'llamacpp' and not args.gguf:
        p.error('--gguf is required for the llamacpp backend')

    if args.backend == 'api' and not args.provider:
        p.error('--provider is required for the api backend')

    if args.backend == 'llamacpp':
        backend, manifest = llamacpp_backend(args.gguf, args.n_ctx, args.threads)
        manifest_sha = manifest['sha256']
    elif args.backend == 'api':
        backend, manifest = api_backend(args.provider, args.model, args.response_format,
                                        args.max_tokens, args.min_interval)
        manifest_sha = None
    else:
        manifest = json.loads(args.manifest.read_text())
        manifest_sha = digest(args.manifest)

        def backend(system, prompt, seed):
            payload = {'model': args.model, 'system': system, 'prompt': prompt, 'stream': False,
                       'format': 'json', 'options': {'temperature': 0, 'seed': seed, 'num_predict': 256}}
            request = urllib.request.Request(args.endpoint+'/api/generate',
                                             data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.load(response)['response']

    args.out.mkdir(parents=True)
    metadata = {'model': args.model, 'backend': args.backend, 'purpose': args.purpose,
                'manifest': manifest, 'manifest_sha256': manifest_sha,
                'endpoint': args.endpoint if args.backend == 'ollama' else manifest.get('endpoint'),
                'seeds': [4088, 4089, 4090, 4091, 4092],
                'temperature': 0, 'num_predict': 256, 'source_sha256': digest(__file__),
                'input_hashes_sha256': digest(args.root/'SHA256SUMS.json'),
                'scope': 'retrospective frozen-input selection audit; no test outcomes in prompts',
                'started_utc_ns': time.time_ns()}
    write(args.out/'plan.json', metadata)

    records = experiment(args.root, backend, metadata['seeds'])
    write(args.out/'records.json', records)
    write(args.out/'heldout.json', heldout(args.root, records))
    valid = sum(r['status'] == 'valid' and r['variant'] == 'full' for r in records)
    write(args.out/'status.json', {'full_valid': valid, 'full_planned': len(metadata['seeds']),
                                 'completed': valid == len(metadata['seeds']),
                                 'purpose': args.purpose,
                                 'llm_effect_established': False,
                                 'note': 'valid outputs alone do not establish an effect; failures are not measurements'})
    print(json.dumps({'out': str(args.out), 'valid_full': valid}))
    return 0 if valid == len(metadata['seeds']) else 2


if __name__ == '__main__':
    raise SystemExit(main())
