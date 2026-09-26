"""Post hoc, partially matched cited-context deletion probe for a finished model audit.

The preregistered faithfulness test in model_audit.py needs a same-kind uncited
control for every cited item. The frozen evidence contains exactly one table, so a
response that cites it is non-estimable there. This probe is added after seeing
that outcome and is reported as exploratory:

* delete_cited:   remove every cited item;
* delete_control: remove the cited non-retrieval items (the table, the graph) and,
                  for each cited retrieval item, one uncited retrieval item (same
                  config first, then evidence order), i.e. a control matched in
                  kind and count except for the unique table/graph items, which
                  both arms delete when cited.

The difference between arms therefore isolates the cited retrieval items only. Test outcomes
are never read. Uses the same prompts, grammar and weights as model_audit.py.
"""
import argparse
import json
from pathlib import Path
import time

from controlled_kernel import digest, write
import model_audit


def controls_for(cited, items):
    uncited = [i for i in items if i['id'] not in cited and i['kind'] == 'retrieval']
    picked = []
    for item in (i for i in items if i['id'] in cited and i['kind'] == 'retrieval'):
        pool = [u for u in uncited if u not in picked]
        same = [u for u in pool if u['config'] == item['config']]
        if not (same or pool):
            return None
        picked.append((same or pool)[0])
    return picked


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path, help='controlled-kernel artifact')
    p.add_argument('audit', type=Path, help='finished model_audit.py output directory')
    p.add_argument('--gguf', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--seed', type=int, default=4088)
    p.add_argument('--threads', type=int, default=4)
    args = p.parse_args()
    if args.out.exists():
        p.error('choose a new output directory')
    plan = json.loads((args.audit/'plan.json').read_text())
    full = next(r for r in json.loads((args.audit/'records.json').read_text())
                if r['variant'] == 'full' and r['seed'] == args.seed and r['status'] == 'valid')
    backend, manifest = model_audit.llamacpp_backend(args.gguf, plan['manifest']['n_ctx'], args.threads)
    if manifest['sha256'] != plan['manifest']['sha256']:
        p.error('weights differ from the audited run')
    _, items = model_audit.evidence(args.root)
    allowed = [c['name'] for c in json.loads((args.root/'plan.json').read_text())['configs']]
    cited = set(full['answer']['cited_ids'])
    controls = controls_for(cited, items)
    args.out.mkdir(parents=True)
    meta = {'model': plan['model'], 'audit': args.audit.name, 'seed': args.seed,
            'weights_sha256': manifest['sha256'], 'source_sha256': digest(__file__),
            'status': 'exploratory post hoc probe; not part of the preregistered audit',
            'full_choice': full['answer']['config'], 'cited': sorted(cited),
            'started_utc_ns': time.time_ns()}
    arms = {'delete_cited': cited}
    if controls is not None:
        by_id = {i['id']: i for i in items}
        arms['delete_control'] = {i for i in cited if by_id[i]['kind'] != 'retrieval'} | {c['id'] for c in controls}
    records = []
    for arm, removed in arms.items():
        context = [i for i in items if i['id'] not in removed]
        prompt = json.dumps({'allowed_configs': allowed, 'evidence': context}, sort_keys=True)
        started = time.monotonic()
        rec = {'arm': arm, 'removed': sorted(removed), 'prompt_sha256': model_audit.hashlib.sha256(prompt.encode()).hexdigest()}
        try:
            raw = backend(model_audit.SYSTEM, prompt, args.seed)
            rec['raw_response'] = raw
            rec['answer'] = model_audit.validate_answer(json.loads(raw), allowed, context)
            rec['status'] = 'valid'
            rec['action_changed'] = rec['answer']['config'] != full['answer']['config']
        except Exception as exc:
            rec.update(status='failed', error_type=type(exc).__name__, error=str(exc))
        rec['elapsed_seconds'] = time.monotonic()-started
        records.append(rec)
    write(args.out/'plan.json', meta)
    write(args.out/'records.json', records)
    print(json.dumps([{k: r.get(k) for k in ('arm', 'status', 'action_changed')} | {'config': r.get('answer', {}).get('config')} for r in records]))


if __name__ == '__main__':
    main()
