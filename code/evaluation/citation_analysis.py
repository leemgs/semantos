#!/usr/bin/env python3
"""Summarize what full-context LLM answers cite in the model audit.

For every valid full-context answer in results/model-audit-*/records.json this
counts citations of the training table, the interaction-graph item, retrieval
runs of the chosen configuration and retrieval runs of other configurations,
and the retrieval block of each cited run. Retrieval items appear in the prompt
in block order (block 0 first), so the block index is also the evidence
position. Every citation count in the paper's citation paragraph comes from here.
"""
import argparse
import collections
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def analyze(records):
    stats = collections.Counter()
    blocks = collections.Counter()
    distinct = set()
    answers = 0
    for r in records:
        if r.get('variant') != 'full' or r.get('status') != 'valid':
            continue
        answers += 1
        answer = r['answer']
        distinct.add(answer['explanation'])
        for cid in answer['cited_ids']:
            stats['citations'] += 1
            if cid == 'training-table':
                stats['table'] += 1
            elif cid == 'interaction':
                stats['graph'] += 1
            elif cid.startswith('retrieval-'):
                _, _period, block, config = cid.split('-', 3)
                blocks[int(block)] += 1
                stats['retrieval_chosen' if config == answer['config'] else 'retrieval_other'] += 1
    return {'answers': answers, 'distinct_explanations': len(distinct), **stats,
            'retrieval_blocks': dict(sorted(blocks.items()))}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--results', default=HERE/'results', type=Path)
    p.add_argument('--out', type=Path, help='write JSON here (default: stdout)')
    a = p.parse_args()
    per_model = {}
    for path in sorted(a.results.glob('model-audit-*/records.json')):
        result = analyze(json.loads(path.read_text()))
        if result['answers']:
            per_model[path.parent.name] = result
    total = collections.Counter()
    blocks = collections.Counter()
    for m in per_model.values():
        total.update({k: v for k, v in m.items() if isinstance(v, int)})
        blocks.update(m['retrieval_blocks'])
    retrieval = sum(blocks.values())
    summary = {
        'models': len(per_model),
        **{k: total[k] for k in ['answers', 'citations', 'table', 'graph', 'retrieval_chosen', 'retrieval_other']},
        'retrieval_citations': retrieval,
        'retrieval_blocks': dict(sorted(blocks.items())),
        'retrieval_in_first_half': sum(v for b, v in blocks.items() if b < 5),
        'models_citing_only_chosen_runs': sum(m.get('retrieval_other', 0) == 0 for m in per_model.values()),
        'models_citing_a_prefix_of_blocks': sorted(
            k for k, m in per_model.items()
            if m['retrieval_blocks'] and list(m['retrieval_blocks']) == list(range(len(m['retrieval_blocks'])))),
        'per_model': per_model,
    }
    text = json.dumps(summary, indent=2) + '\n'
    if a.out:
        a.out.write_text(text)
    else:
        print(text, end='')


if __name__ == '__main__':
    main()
