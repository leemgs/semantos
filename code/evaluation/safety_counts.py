"""Count independent action labels separately from gate and rollout events.

Input: one JSON object per unique bundle, with decision=accepted|vetoed|invalid,
unsafe=true|false|null and rolled_back=true|false. Null labels stay unknown.
"""
import argparse
from collections import Counter
import json
from pathlib import Path


def summarize(rows):
    counts=Counter(proposed=0,accepted=0,vetoed=0,invalid=0,unknown=0,tp=0,fp=0,fn=0,tn=0,
                   rolled_back=0,unsafe_rolled_back=0,labeled_rolled_back=0)
    seen=set()
    for row in rows:
        rid=row['bundle_id'];decision=row['decision'];y=row['unsafe'];rb=row['rolled_back']
        if rid in seen or not rid or decision not in {'accepted','vetoed','invalid'}:
            raise ValueError('duplicate bundle or invalid decision')
        if (y is not None and type(y) is not bool) or type(rb) is not bool:
            raise ValueError('unsafe and rolled_back must be boolean (unsafe may be null)')
        if rb and decision!='accepted':raise ValueError('only executed accepted bundles can roll back')
        seen.add(rid);counts['proposed']+=1;counts[decision]+=1
        if rb:
            counts['rolled_back']+=1
            counts['labeled_rolled_back']+=int(y is not None)
            counts['unsafe_rolled_back']+=int(y is True)
        if y is None:counts['unknown']+=1;continue
        if decision=='invalid':continue
        counts[('tp' if y else 'fp') if decision=='vetoed' else ('fn' if y else 'tn')]+=1
    def ratio(a,b):return a/b if b else None
    return {'counts':dict(counts),
            'unsafe_given_accepted':ratio(counts['fn'],counts['fn']+counts['tn']),
            'acceptance_given_unsafe':ratio(counts['fn'],counts['fn']+counts['tp']),
            'veto_given_safe':ratio(counts['fp'],counts['fp']+counts['tn']),
            'veto_precision':ratio(counts['tp'],counts['tp']+counts['fp']),
            'rollback_precision_labeled_only':ratio(counts['unsafe_rolled_back'],counts['labeled_rolled_back']),
            'note':'conditional metrics use labeled bundles only; missing-label selection may bias them'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('jsonl',type=Path);a=p.parse_args()
    print(json.dumps(summarize([json.loads(s) for s in a.jsonl.read_text().splitlines() if s]),indent=2))
