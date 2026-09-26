"""Run matched-context model ablations and context-deletion interventions.

Uses only train/retrieval inputs from a controlled-kernel artifact. No model result
is inferred from a failed backend, and test outcomes are never sent to the model.
This narrow configuration-selection task is not the REST VM-sysctl deployment.
"""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import time
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


def llamacpp_backend(path, n_ctx, threads):
    from llama_cpp import Llama, __version__ as llama_cpp_version
    model = Llama(model_path=str(path), n_ctx=n_ctx, n_threads=threads, verbose=False)
    meta = {k: v for k, v in model.metadata.items() if k.startswith('general.')}

    def backend(system, prompt, seed):
        # Constrained decoding: the grammar fixes the answer's shape and restricts
        # `config` to the allowed names and citations to the supplied evidence IDs
        # (still re-checked afterwards). Model-only prompts carry no evidence to cite.
        context = json.loads(prompt)
        allowed, ids = context['allowed_configs'], [e['id'] for e in context['evidence']]
        cite = {'type': 'string', 'enum': ids} if ids else {'type': 'string'}
        schema = {'type': 'object', 'required': ['config', 'cited_ids', 'explanation'],
                  'properties': {'config': {'type': 'string', 'enum': allowed},
                                 'cited_ids': {'type': 'array', 'items': cite, 'maxItems': 6 if ids else 0},
                                 'explanation': {'type': 'string', 'maxLength': 400}}}
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
    p.add_argument('--backend', choices=['ollama', 'llamacpp'], default='ollama')
    p.add_argument('--model', required=True, help='model name recorded in plan.json')
    p.add_argument('--manifest', type=Path, help='ollama: local manifest for the exact installed model')
    p.add_argument('--endpoint', default='http://127.0.0.1:11434')
    p.add_argument('--gguf', type=Path, help='llamacpp: path to the GGUF weights (hashed into the plan)')
    p.add_argument('--n-ctx', type=int, default=8192)
    p.add_argument('--threads', type=int, default=4)
    p.add_argument('--purpose', default='experiment', choices=['experiment', 'pipeline-check'],
                   help='pipeline-check runs are plumbing tests and must not be reported as results')
    args = p.parse_args()
    if args.out.exists():
        p.error('choose a new output directory')
    if args.backend == 'ollama' and not args.manifest:
        p.error('--manifest is required for the ollama backend')
    if args.backend == 'llamacpp' and not args.gguf:
        p.error('--gguf is required for the llamacpp backend')

    if args.backend == 'llamacpp':
        backend, manifest = llamacpp_backend(args.gguf, args.n_ctx, args.threads)
        manifest_sha = manifest['sha256']
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
                'endpoint': args.endpoint if args.backend == 'ollama' else None,
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
