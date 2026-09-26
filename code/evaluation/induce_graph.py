"""Induce scoped empirical interaction edges from independent measured sweeps.

Each input row: id, split=train, source=measured, group, pair=[a,b], run,
losses={baseline,a,b,joint}. Lower loss is better. Each run must contain the
four configurations under a matched acquisition block. No target effect sizes.
"""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import numpy as np


def induce(rows, seed=4088, n_boot=2000):
    groups=defaultdict(list);ids=set();runs=set()
    for row in rows:
        if row['split']!='train' or row['source']!='measured':
            raise ValueError('only independently measured training sweeps are allowed')
        if row['id'] in ids:raise ValueError('duplicate source id')
        ids.add(row['id'])
        pair=tuple(row['pair'])
        if len(pair)!=2 or pair[0]==pair[1]:raise ValueError('distinct pair required')
        key=(row['group'],pair); run=(*key,row['run'])
        if run in runs:raise ValueError('duplicate run within pair and scope')
        runs.add(run)
        loss=row['losses'];values=[loss[k] for k in ['baseline','a','b','joint']]
        if not all(np.isfinite(x) and x>=0 for x in values):raise ValueError('invalid losses')
        if loss['baseline']<=0:raise ValueError('positive baseline required for normalization')
        contrast=(loss['joint']-loss['a']-loss['b']+loss['baseline'])/loss['baseline']
        groups[key].append((contrast,row['id']))
    rng=np.random.default_rng(seed);edges=[]
    for (scope,pair),values in sorted(groups.items()):
        if len(values)<10:raise ValueError('at least 10 independent sweep runs per pair required')
        x=np.array([v for v,_ in values])
        boot=rng.choice(x,(n_boot,len(x)),replace=True).mean(axis=1)
        lo,hi=np.quantile(boot,[.025,.975])
        if lo<=0<=hi:continue
        beneficial=hi<0
        edges.append({'from':pair[0],'to':pair[1],
                      'edge_type':'synergizes_with' if beneficial else 'conflicts_with',
                      'sign':1 if beneficial else -1,'weight':min(1.,abs(float(x.mean()))),
                      'evidence':len(x),'scope':scope,'normalized_interaction':float(x.mean()),
                      'ci95':[float(lo),float(hi)],'source_ids':[rid for _,rid in values],
                      'interpretation':'empirical interaction; not a universal causal or admissibility rule'})
    return edges

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('jsonl',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.jsonl.read_bytes();edges=induce([json.loads(s) for s in raw.splitlines() if s])
    a.out.write_text(json.dumps({'input_sha256':hashlib.sha256(raw).hexdigest(),'edges':edges},indent=2))
