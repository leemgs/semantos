"""Run matched-context model ablations and context-deletion interventions.

Uses only train/retrieval inputs from a controlled-kernel artifact. No model result
is inferred from a failed backend, and test outcomes are never sent to the model.
This narrow configuration-selection task is not the REST VM-sysctl deployment.
"""
import argparse
import hashlib
import json
from pathlib import Path
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


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--model', required=True)
    p.add_argument('--manifest', type=Path, required=True, help='local Ollama manifest for exact installed model')
    p.add_argument('--endpoint', default='http://127.0.0.1:11434')
    args = p.parse_args()
    if args.out.exists():
        p.error('choose a new output directory')
    args.out.mkdir(parents=True)
    manifest = json.loads(args.manifest.read_text())
    metadata = {'model': args.model, 'manifest': manifest, 'manifest_sha256': digest(args.manifest),
                'endpoint': args.endpoint, 'seeds': [4088, 4089, 4090, 4091, 4092],
                'temperature': 0, 'num_predict': 256, 'source_sha256': digest(__file__),
                'input_hashes_sha256': digest(args.root/'SHA256SUMS.json'),
                'scope': 'retrospective frozen-input selection audit; no test outcomes in prompts',
                'started_utc_ns': time.time_ns()}
    write(args.out/'plan.json', metadata)

    def backend(system, prompt, seed):
        payload = {'model': args.model, 'system': system, 'prompt': prompt, 'stream': False,
                   'format': 'json', 'options': {'temperature': 0, 'seed': seed, 'num_predict': 256}}
        request = urllib.request.Request(args.endpoint+'/api/generate',
                                         data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.load(response)['response']

    records = experiment(args.root, backend, metadata['seeds'])
    write(args.out/'records.json', records)
    valid = sum(r['status'] == 'valid' and r['variant'] == 'full' for r in records)
    write(args.out/'status.json', {'full_valid': valid, 'full_planned': len(metadata['seeds']),
                                 'completed': valid == len(metadata['seeds']),
                                 'llm_effect_established': False,
                                 'note': 'valid outputs alone do not establish an effect; failures are not measurements'})
    print(json.dumps({'out': str(args.out), 'valid_full': valid}))
    return 0 if valid == len(metadata['seeds']) else 2


if __name__ == '__main__':
    raise SystemExit(main())
