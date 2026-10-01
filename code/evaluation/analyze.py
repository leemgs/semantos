"""Summarize measured operation logs, with uncertainty across independent runs."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from collections import defaultdict
import numpy as np
from scipy.stats import t


def analyze(folder):
    manifest=json.loads((folder/'manifest.json').read_text())
    raw=(folder/'operations.csv').read_bytes()
    if manifest.get('kind')!='measured_local_baseline' or hashlib.sha256(raw).hexdigest()!=manifest.get('raw_sha256'):
        raise ValueError('measured provenance or raw hash mismatch')
    groups=defaultdict(list)
    with (folder/'operations.csv').open() as f:
        for row in csv.DictReader(f):groups[row['workload'],int(row['run'])].append(row)
    by_workload=defaultdict(list)
    for (w,r),rows in groups.items():
        lat=np.array([float(x['latency_ms']) for x in rows])
        if not np.all(np.isfinite(lat)) or np.any(lat<0):raise ValueError('invalid latency')
        if len(rows)!=manifest['operations_per_run']:raise ValueError('incomplete run')
        errors=sum(int(x['error']) for x in rows)
        anomalies=sum(int(x['error'])==1 or float(x['latency_ms'])>float(x['deadline_ms']) for x in rows)
        by_workload[w].append({'run':r,'median_ms':float(np.median(lat)),
                               'p95_ms':float(np.quantile(lat,.95)),
                               'anomaly_rate':anomalies/len(rows),'errors':errors,'operations':len(rows)})
    result={'kind':'measured_local_baseline','raw_sha256':manifest['raw_sha256'],'workloads':{}}
    for w,runs in by_workload.items():
        if len(runs)!=manifest['runs']:raise ValueError('incomplete repetitions')
        stats={}
        for metric in ['median_ms','p95_ms','anomaly_rate']:
            x=np.array([r[metric] for r in runs]);mean=float(x.mean())
            half=float(t.ppf(.975,len(x)-1)*x.std(ddof=1)/np.sqrt(len(x)))
            stats[metric]={'mean':mean,'ci95_half_width':half,'n_runs':len(x)}
        result['workloads'][w]={'statistics':stats,'runs':sorted(runs,key=lambda r:r['run'])}
    (folder/'summary.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    lines=['# Measured local baseline','', 'No kernel intervention or controller comparison was performed.','',
           '| Workload | Runs | Median ms (mean ± 95% CI) | P95 ms (mean ± 95% CI) | Deadline/error fraction |',
           '|---|---:|---:|---:|---:|']
    tex=[]
    for w,v in sorted(result['workloads'].items()):
        s=v['statistics'];m=s['median_ms'];q=s['p95_ms'];a=s['anomaly_rate']
        lines.append(f"| {w} | {m['n_runs']} | {m['mean']:.4f} ± {m['ci95_half_width']:.4f} | {q['mean']:.4f} ± {q['ci95_half_width']:.4f} | {a['mean']:.4f} |")
        label=w.replace('_',r'\_')
        tex.append(f"{label} & {m['mean']:.3f} & {q['mean']:.3f} $\\pm$ {q['ci95_half_width']:.3f} & {100*a['mean']:.2f} \\\\")
    (folder/'summary.md').write_text('\n'.join(lines)+'\n')
    (folder/'table.tex').write_text(r'\begin{tabular}{lrrr}'+'\n'+r'\toprule'+'\n'+r'Workload & Median ms & P95 ms & Events \% \\'+'\n'+r'\midrule'+'\n'+'\n'.join(tex)+'\n'+r'\bottomrule'+'\n'+r'\end{tabular}'+'\n')
    print('\n'.join(lines))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);args=p.parse_args();analyze(args.folder)
