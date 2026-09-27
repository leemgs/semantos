"""Summarize one or more model-audit runs (plan/records/heldout) into Markdown and LaTeX.

Reads only files written by model_audit.py. A run whose plan says
purpose=pipeline-check is refused, so plumbing tests cannot enter the paper.
"""
import argparse
import collections
import json
from pathlib import Path
import re

VARIANTS = ['full', 'no_graph', 'no_retrieval', 'model_only', 'delete_cited', 'delete_uncited']
PRETTY = {'s50000_aall': '50\\,$\\mu$s/all', 's50000_aone': '50\\,$\\mu$s/one',
          's1000000_aall': '1\\,ms/all', 's1000000_aone': '1\\,ms/one'}


def load(run):
    plan = json.loads((run/'plan.json').read_text())
    if plan.get('purpose') != 'experiment':
        raise SystemExit(f'{run}: not an experiment run')
    records = json.loads((run/'records.json').read_text())
    heldout = json.loads((run/'heldout.json').read_text())
    return plan, records, heldout


def numbers_grounded(record):
    """Decimal numbers quoted in the explanation that occur verbatim in the prompt.

    A lexical check only: a number can occur in the evidence yet be attributed to
    the wrong item, which this does not detect."""
    found = re.findall(r'\d+\.\d+', record['answer']['explanation'])
    return len(found), sum(n in record['prompt'] for n in found)


def summarize(run):
    plan, records, heldout = load(run)
    calls = [r for r in records if r['variant'] in VARIANTS]
    by_variant = collections.OrderedDict()
    for v in VARIANTS:
        rows = [r for r in calls if r['variant'] == v]
        if not rows:
            continue
        valid = [r for r in rows if r['status'] == 'valid']
        by_variant[v] = {'calls': len(rows), 'valid': len(valid),
                         'choices': dict(collections.Counter(r['answer']['config'] for r in valid)),
                         'mean_citations': (sum(len(r['answer']['cited_ids']) for r in valid)/len(valid)) if valid else None,
                         'cites_training_table': sum('training-table' in r['answer']['cited_ids'] for r in valid),
                         'cites_graph': sum('interaction' in r['answer']['cited_ids'] for r in valid),
                         'decimal_numbers_quoted': sum(numbers_grounded(r)[0] for r in valid),
                         'decimal_numbers_in_prompt': sum(numbers_grounded(r)[1] for r in valid)}
    faith = [r for r in records if r['variant'] == 'faithfulness']
    scored = collections.OrderedDict()
    for h in heldout:
        key = (h['config'], h['period_ms'])
        scored.setdefault(key, h)
    probe_dir = run/'probe-cited-deletion'
    probe = None
    if probe_dir.exists():
        probe = {'status': json.loads((probe_dir/'plan.json').read_text())['status'],
                 'arms': [{k: r.get(k) for k in ('arm', 'status', 'action_changed', 'removed')}
                          | {'config': r.get('answer', {}).get('config')}
                          for r in json.loads((probe_dir/'records.json').read_text())]}
    elapsed = [r['elapsed_seconds'] for r in calls]
    manifest = plan['manifest']
    return {'run': run.name, 'model': plan['model'], 'sha256': manifest.get('sha256'),
            'shards': manifest.get('shards'), 'runtime': manifest.get('runtime'),
            'seeds': plan['seeds'], 'variants': by_variant,
            'faithfulness': {'valid': sum(f['status'] == 'valid' for f in faith),
                             'not_estimable': sum(f['status'] == 'not_estimable' for f in faith),
                             'cited_action_changed': sum(f.get('cited_action_changed', False) for f in faith),
                             'uncited_action_changed': sum(f.get('uncited_action_changed', False) for f in faith),
                             'records': faith},
            'heldout_by_choice': [{'config': c, 'period_ms': ms, 'p95_us': h['p95_us'],
                                   'reduction_pct': h['reduction_pct'], 'same_as_control': h['same_as_control']}
                                  for (c, ms), h in scored.items()],
            'probe': probe, 'calls': len(calls), 'valid_calls': sum(r['status'] == 'valid' for r in calls),
            'elapsed_seconds_total': sum(elapsed),
            'elapsed_seconds_mean': sum(elapsed)/len(elapsed) if elapsed else None}


def markdown(summaries):
    out = ['# Model audit summary', '',
           'Retrospective frozen-input selection audit on the controlled follow-up. Prompts contain',
           'training and retrieval evidence only; held-out outcomes are read after all calls.', '']
    for s in summaries:
        out += [f"## {s['model']}", '', f"Weights SHA-256: `{s['sha256']}`; runtime {s['runtime']}; "
                f"seeds {s['seeds']}; {s['valid_calls']}/{s['calls']} valid calls, "
                f"{s['elapsed_seconds_total']:.0f} s total ({s['elapsed_seconds_mean']:.1f} s/call).", '',
                '| Variant | Valid/calls | Choices | Mean citations | Cites table | Cites graph | Quoted decimals in prompt |',
                '|---|---|---|---|---|---|---|']
        for v, d in s['variants'].items():
            mc = '-' if d['mean_citations'] is None else f"{d['mean_citations']:.1f}"
            out.append(f"| {v} | {d['valid']}/{d['calls']} | {d['choices']} | {mc} | "
                       f"{d['cites_training_table']} | {d['cites_graph']} | "
                       f"{d['decimal_numbers_in_prompt']}/{d['decimal_numbers_quoted']} |")
        f = s['faithfulness']
        if s['probe']:
            out += ['', f"Probe ({s['probe']['status']}): " + '; '.join(
                f"{a['arm']} -> {a['config']} (changed: {a['action_changed']})" for a in s['probe']['arms']) + '.']
        out += ['', f"Faithfulness: {f['valid']} estimable seeds, {f['not_estimable']} not estimable; "
                f"action changed after deleting cited context in {f['cited_action_changed']}, "
                f"after deleting matched uncited context in {f['uncited_action_changed']}.", '',
                '| Chosen config | Period ms | Test P95 us ± 95% CI | Paired reduction % ± 95% CI |',
                '|---|---|---|---|']
        for h in s['heldout_by_choice']:
            out.append(f"| {h['config']} | {h['period_ms']} | {h['p95_us']['mean']:.1f} ± "
                       f"{h['p95_us']['ci95_halfwidth']:.1f} | {h['reduction_pct']['mean']:.1f} ± "
                       f"{h['reduction_pct']['ci95_halfwidth']:.1f} |")
        out.append('')
    out.append('Valid outputs and unchanged choices are not an LLM advantage; five seeds under greedy '
               'decoding are not independent samples.')
    return '\n'.join(out) + '\n'


def latex(summaries):
    """Compact table: per model, contexts grouped by their (seed-invariant) choice."""
    short = {'Qwen2.5-7B-Instruct-Q4_K_M': 'Qwen-7B', 'Meta-Llama-3.1-8B-Instruct-Q4_K_M': 'Llama-8B',
             'Qwen2.5-14B-Instruct-Q4_K_M': 'Qwen-14B', 'phi-4-Q4_K': 'Phi-4'}
    abbrev = {'full': 'full', 'no_graph': 'no graph', 'no_retrieval': 'no retr.', 'model_only': 'none',
              'delete_cited': 'del.\\ cited', 'delete_uncited': 'del.\\ unc.'}
    rows = []
    for s in summaries:
        replay = {(h['config'], h['period_ms']): h['reduction_pct'] for h in s['heldout_by_choice']}
        periods = sorted({ms for _, ms in replay})
        groups = collections.OrderedDict()
        for v, d in s['variants'].items():
            if len(d['choices']) != 1 or d['valid'] != d['calls']:
                raise SystemExit(f"{s['model']} {v}: invalid calls or seed-dependent choice; extend the table")
            groups.setdefault(next(iter(d['choices'])), []).append(abbrev[v])
        for k, (config, contexts) in enumerate(groups.items()):
            cells = []
            for ms in periods:
                r = replay[config, ms]
                cells.append('0' if r['mean'] == 0 and r['ci95_halfwidth'] == 0
                             else f"${r['mean']:.0f}\\pm{r['ci95_halfwidth']:.0f}$")
            name = short.get(s['model'], s['model']) if k == 0 else ''
            if contexts[:4] == ['full', 'no graph', 'no retr.', 'none']:
                contexts = ['all four'] + contexts[4:]
            elif contexts[:3] == ['full', 'no graph', 'no retr.']:
                contexts = ['evid.' if contexts[3:] else 'evidence'] + contexts[3:]
            label = ', '.join(contexts)
            rows.append(f"{name} & {label} & {PRETTY.get(config, config)} & " + ' & '.join(cells) + ' \\\\')
        rows.append('\\addlinespace[2pt]')
    return ('\\begin{tabular}{@{}llccc@{}}\n\\toprule\n'
            'Model & Context & Choice & 5\\,ms & 8\\,ms \\\\\n\\midrule\n'
            + '\n'.join(rows[:-1]) + '\n\\bottomrule\n\\end{tabular}\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('runs', type=Path, nargs='+')
    p.add_argument('--out', type=Path, required=True, help='directory for summary.json/summary.md')
    p.add_argument('--tex', type=Path, help='LaTeX table path')
    args = p.parse_args()
    summaries = [summarize(r) for r in args.runs]
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out/'summary.json').write_text(json.dumps(summaries, indent=2) + '\n')
    (args.out/'summary.md').write_text(markdown(summaries))
    if args.tex:
        args.tex.write_text(latex(summaries))
    print((args.out/'summary.md').read_text())


if __name__ == '__main__':
    main()
