#!/usr/bin/env python3
"""Tabulate the manual explanation-claim audit by model and error type.

Reads results/model-audit-summary/claim-audit.json (one record per audited
quantitative or comparative claim, labeled by the authors against the supplied
prompt evidence) and writes the LaTeX rows used by the paper's claim table.
Every count in that table is recomputed here from the per-claim labels.
"""
import argparse
import collections
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCAL = ['Qwen2.5-7B', 'Llama-3.1-8B', 'Qwen2.5-14B', 'Phi-4']
HOSTED = ['Llama-3.3-70B', 'Qwen3-235B', 'DeepSeek-V3.2', 'Nemotron-3-Ultra-550B',
          'Gemini-3.8-Flash', 'Gemini-3.1-Pro']
SHORT = {'Qwen2.5-7B': 'Qwen-7B', 'Llama-3.1-8B': 'Llama-8B', 'Qwen2.5-14B': 'Qwen-14B',
         'Phi-4': 'Phi-4', 'Llama-3.3-70B': 'Llama-70B', 'Qwen3-235B': 'Qwen3-235B',
         'DeepSeek-V3.2': 'DeepSeek-V3.2', 'Nemotron-3-Ultra-550B': 'Nemotron-550B',
         'Gemini-3.8-Flash': 'Gemini-Flash', 'Gemini-3.1-Pro': 'Gemini-Pro'}
# Columns: correct; overstated; wrong value (incl. partly wrong); wrong unit or
# source attribution; unsupported prior (no-evidence prompts only).
COLUMNS = [('correct',), ('overstated',), ('wrong', 'partly wrong'),
           ('wrong unit', 'wrong attribution'), ('unsupported prior',)]
# "Misstated" follows the paper's definition: wrong, misattributed, overstated or
# wrong unit; "partly wrong" and unsupported priors are excluded.
MISSTATED = {'wrong', 'wrong attribution', 'overstated', 'wrong unit'}


def row(label, claims):
    c = collections.Counter(x['verdict'] for x in claims)
    cells = [sum(c[v] for v in col) for col in COLUMNS]
    mis = sum(c[v] for v in MISSTATED)
    return label, len(claims), cells, mis


def fmt(r, bold=False):
    label, n, cells, mis = r
    vals = [str(n)] + [str(v) if v else '--' for v in cells] + [str(mis)]
    if bold:
        label, vals = f'\\textit{{{label}}}', [f'\\textit{{{v}}}' for v in vals]
    return ' & '.join([label] + vals) + r' \\'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--audit', default=HERE/'results/model-audit-summary/claim-audit.json', type=Path)
    p.add_argument('--out', type=Path, help='write the LaTeX tabular here (default: stdout)')
    a = p.parse_args()
    claims = json.loads(a.audit.read_text())['claims']
    known = set(LOCAL) | set(HOSTED)
    unknown = {x['model'] for x in claims} - known
    if unknown:
        raise SystemExit(f'unknown models in audit: {sorted(unknown)}')
    lines = [r'\begin{tabular}{@{}lrrrrrrr@{}}', r'\toprule',
             r'Model & $n$ & Corr. & Over. & Wrong & Unit/Src & Prior & Misst. \\', r'\midrule']
    for group, models in [('Local, all variants', LOCAL), ('Hosted, full context', HOSTED)]:
        for m in models:
            lines.append(fmt(row(SHORT[m], [x for x in claims if x['model'] == m])))
        lines.append(fmt(row(group, [x for x in claims if x['model'] in models]), bold=True))
        lines.append(r'\midrule' if group.startswith('Local') else r'\bottomrule')
    lines.append(r'\end{tabular}')
    text = '\n'.join(lines) + '\n'
    if a.out:
        a.out.write_text(text)
    else:
        print(text, end='')


if __name__ == '__main__':
    main()
