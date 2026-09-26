"""Verify immutable measurement inputs and summarize paired held-out blocks."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics


def p95(row):
    v=sorted(e['lateness_ns']/1000 for e in row['events'])
    return v[math.ceil(.95*len(v))-1]


def analyze(root):
    hashes=json.loads((root/'SHA256SUMS.json').read_text())
    for name,digest in hashes.items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('hash mismatch: '+name)
    plan=json.loads((root/'plan.json').read_text())
    chosen=json.loads((root/'frozen-selection.json').read_text())
    rows=[json.loads(s) for s in (root/'runs.jsonl').read_text().splitlines()]
    expected={(role,b,period,c['name']) for role in ['train','test'] for b in range(plan[role+'_blocks']) for period in plan['periods_ns'] for c in plan['configs']}
    keys=[(r['role'],r['block'],r['period_ns'],r['name']) for r in rows]
    if len(keys)!=len(set(keys)) or set(keys)!=expected: raise ValueError('incomplete/duplicate runs')
    for r in rows:
        if len(r['events'])!=plan['samples']:raise ValueError('incomplete events')
        if r['readback_slack_ns']!=r['slack_ns'] or r['readback_cpus']!=r['cpus']:raise ValueError('readback mismatch')
        if any(e['lateness_ns']!=max(0,e['observed_ns']-e['target_ns']) for e in r['events']):raise ValueError('timing mismatch')
    summary=[]
    for period in plan['periods_ns']:
        training={c['name']:statistics.mean(p95(r) for r in rows if r['role']=='train' and r['period_ns']==period and r['name']==c['name']) for c in plan['configs']}
        if min(training,key=training.get)!=chosen[str(period)]: raise ValueError('selection mismatch')
        for c in plan['configs']:
            test=sorted([r for r in rows if r['role']=='test' and r['period_ns']==period and r['name']==c['name']],key=lambda r:r['block'])
            baseline=sorted([r for r in rows if r['role']=='test' and r['period_ns']==period and r['name']==plan['control']],key=lambda r:r['block'])
            values=[p95(r) for r in test]
            differences=[p95(r)-p95(b) for r,b in zip(test,baseline)]
            summary.append({'period_ms':period/1e6,'config':c['name'],'selected':c['name']==chosen[str(period)],'mean_p95_us':statistics.mean(values),'ci95_halfwidth_us':2.262157*statistics.stdev(values)/math.sqrt(len(values)), 'paired_delta_us':statistics.mean(differences),'paired_delta_ci95_us':2.262157*statistics.stdev(differences)/math.sqrt(len(differences)), 'late_events':sum(e['lateness_ns']>plan['deadline_ns'] for r in test for e in r['events']), 'events':sum(len(r['events']) for r in test)})
    (root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    lines=['| Period ms | Config | Train-selected | Mean run P95 us (95% CI halfwidth) | Paired delta us (95% CI halfwidth) | >200 us |','|---|---|---|---|---|---|']
    tex=['\\begin{tabular}{rlrr}','\\toprule','Period & Slack/CPUs & P95 ($\\mu$s) & Misses \\\\','\\midrule']
    for r in summary:
        lines.append(f"| {r['period_ms']:g} | {r['config']} | {r['selected']} | {r['mean_p95_us']:.1f} +/- {r['ci95_halfwidth_us']:.1f} | {r['paired_delta_us']:.1f} +/- {r['paired_delta_ci95_us']:.1f} | {r['late_events']}/{r['events']} |")
        label=r['config'].replace('slack50000','50us').replace('slack1000000','1ms').replace('_','/')
        tex.append(f"{r['period_ms']:g} & {label} & {r['mean_p95_us']:.1f} & {r['late_events']}/{r['events']} \\\\")
    tex+=['\\bottomrule','\\end{tabular}']
    (root/'summary.md').write_text('\n'.join(lines)+'\n')
    (root/'table.tex').write_text('\n'.join(tex)+'\n')
    print('\n'.join(lines))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);analyze(p.parse_args().root)
