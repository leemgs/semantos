#!/usr/bin/env python3
"""Re-analyse the existing audit records by model scale and family.

No new model calls: decisions and citations come from results/model-audit-*/
records.json, claim labels from results/model-audit-summary/claim-audit.json.
Only the full-context variant is used, because local models were also audited
on ablated prompts while hosted models were audited on full context only;
mixing variants would confound scale with prompt condition.

Per model it reports: full-context answers that pick the selector's
configuration, citations of retrieval runs of the chosen configuration and of
the first half of the evidence list (blocks 0-4), audited claims, misstated
claims (paper definition) and their type. Groups: local 7-14B open weights,
hosted 70B-671B open weights, proprietary. For the eight open-weight models it
gives Spearman's rho between log total parameters and the misstated share, and
Fisher's exact test of local versus hosted open-weight misstatement.

    python3 scale_family_analysis.py --out results/model-audit-summary/scale-family.json \
        --tex ../../paper/scale-family.tex
"""
import argparse
import collections
import json
import math
from pathlib import Path

from scipy import stats

HERE = Path(__file__).resolve().parent
RES = HERE/'results'
SELECTOR_CHOICE = 's50000_aall'
MISSTATED = {'wrong', 'wrong attribution', 'overstated', 'wrong unit'}
# name, result directory, family, total parameters (billions; None = undisclosed), group
MODELS = [
    ('Qwen2.5-7B', 'qwen2.5-7b', 'Qwen', 7.6, 'local'),
    ('Llama-3.1-8B', 'llama3.1-8b', 'Llama', 8.0, 'local'),
    ('Qwen2.5-14B', 'qwen2.5-14b', 'Qwen', 14.7, 'local'),
    ('Phi-4', 'phi-4', 'Phi', 14.7, 'local'),
    ('Llama-3.3-70B', 'api-llama3.3-70b', 'Llama', 70.6, 'hosted open'),
    ('Qwen3-235B', 'api-qwen3-235b', 'Qwen', 235.0, 'hosted open'),
    ('DeepSeek-V3.2', 'api-deepseek-v3.2', 'DeepSeek', 671.0, 'hosted open'),
    ('Nemotron-3-Ultra-550B', 'api-nemotron3-ultra-550b', 'Nemotron', 550.0, 'hosted open'),
    ('Gemini-3.8-Flash', 'api-gemini-3.8-flash', 'Gemini', None, 'proprietary'),
    ('Gemini-3.1-Pro', 'api-gemini-3.1-pro', 'Gemini', None, 'proprietary'),
]
SHORT = {'Qwen2.5-7B': 'Qwen-7B', 'Llama-3.1-8B': 'Llama-8B', 'Qwen2.5-14B': 'Qwen-14B', 'Phi-4': 'Phi-4',
         'Llama-3.3-70B': 'Llama-70B', 'Qwen3-235B': 'Qwen3-235B', 'DeepSeek-V3.2': 'DeepSeek-V3.2',
         'Nemotron-3-Ultra-550B': 'Nemotron-550B', 'Gemini-3.8-Flash': 'Gemini-Flash', 'Gemini-3.1-Pro': 'Gemini-Pro'}
GROUPS = [('local', 'Local open, 7--15B'), ('hosted open', 'Hosted open, 70--671B'), ('proprietary', 'Proprietary')]


def per_model(claims):
    rows = []
    for name, d, family, params, group in MODELS:
        recs = [r for r in json.loads((RES/f'model-audit-{d}/records.json').read_text())
                if r.get('variant') == 'full' and r.get('status') == 'valid']
        evidence = {e['id']: e for e in json.loads(recs[0]['prompt'])['evidence']}
        order = [e['id'] for e in json.loads(recs[0]['prompt'])['evidence'] if e['kind'] == 'retrieval']
        runs = [evidence[x] for r in recs for x in r['answer']['cited_ids']
                if x in evidence and evidence[x]['kind'] == 'retrieval']
        chosen = [r['answer']['config'] for r in recs]
        cited_chosen = sum(e['config'] == c for r, c in zip(recs, chosen) for x in r['answer']['cited_ids']
                           if x in evidence and (e := evidence[x])['kind'] == 'retrieval')
        first_half = sum(order.index(e['id']) < len(order) / 2 for e in runs)
        cl = [c for c in claims if c['model'] == name and c['variant'] == 'full']
        types = collections.Counter(c['verdict'] for c in cl)
        rows.append({'model': name, 'family': family, 'params_b': params, 'group': group,
                     'answers': len(recs), 'selector_choice': sum(c == SELECTOR_CHOICE for c in chosen),
                     'retrieval_citations': len(runs), 'cited_chosen_config': cited_chosen,
                     'cited_first_half': first_half, 'claims': len(cl),
                     'misstated': sum(types[v] for v in MISSTATED), 'overstated': types['overstated'],
                     'wrong_value': types['wrong'] + types['partly wrong'],
                     'unit_or_source': types['wrong unit'] + types['wrong attribution']})
    return rows


def aggregate(rows):
    keys = ['answers', 'selector_choice', 'retrieval_citations', 'cited_chosen_config', 'cited_first_half',
            'claims', 'misstated', 'overstated', 'wrong_value', 'unit_or_source']
    return {k: sum(r[k] for r in rows) for k in keys} | {'models': len(rows)}


def frac(a, b):
    return f'{a}/{b}' if b else '--'


def write_tex(rows, groups, path):
    lines = [r'\begin{tabular}{@{}lrrrrrr@{}}', r'\toprule',
             r'Model & Params & Sel. & Cited chosen & First half & Misst. & Over./Val./Unit \\', r'\midrule']
    for g, title in GROUPS:
        for r in [x for x in rows if x['group'] == g]:
            p = f"{r['params_b']:g}B" if r['params_b'] else '--'
            lines.append(f"{SHORT[r['model']]} & {p} & {r['selector_choice']}/{r['answers']} & "
                         f"{frac(r['cited_chosen_config'], r['retrieval_citations'])} & "
                         f"{frac(r['cited_first_half'], r['retrieval_citations'])} & {frac(r['misstated'], r['claims'])} & "
                         f"{r['overstated']}/{r['wrong_value']}/{r['unit_or_source']} \\\\")
        a = groups[g]
        lines.append(f"\\textit{{{title}}} & & \\textit{{{a['selector_choice']}/{a['answers']}}} & "
                     f"\\textit{{{frac(a['cited_chosen_config'], a['retrieval_citations'])}}} & "
                     f"\\textit{{{frac(a['cited_first_half'], a['retrieval_citations'])}}} & "
                     f"\\textit{{{frac(a['misstated'], a['claims'])}}} & "
                     f"\\textit{{{a['overstated']}/{a['wrong_value']}/{a['unit_or_source']}}} \\\\")
        if g != GROUPS[-1][0]:
            lines.append(r'\midrule')
    lines += [r'\bottomrule', r'\end{tabular}']
    path.write_text('\n'.join(lines) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--tex', type=Path)
    a = ap.parse_args()
    claims = json.loads((RES/'model-audit-summary/claim-audit.json').read_text())['claims']
    rows = per_model(claims)
    groups = {g: aggregate([r for r in rows if r['group'] == g]) for g, _ in GROUPS}
    families = {f: aggregate([r for r in rows if r['family'] == f]) for f in dict.fromkeys(r['family'] for r in rows)}
    open_rows = [r for r in rows if r['params_b'] and r['claims']]
    rho, p_rho = stats.spearmanr([math.log(r['params_b']) for r in open_rows],
                                 [r['misstated'] / r['claims'] for r in open_rows])
    loc, hos = groups['local'], groups['hosted open']
    odds, p_fisher = stats.fisher_exact([[loc['misstated'], loc['claims'] - loc['misstated']],
                                         [hos['misstated'], hos['claims'] - hos['misstated']]])
    out = {'scope': 'full-context answers only (5 per model); claims audited on the full-context variant',
           'per_model': rows, 'groups': groups, 'families': families,
           'spearman_logparams_vs_misstated_share': {'models': len(open_rows), 'rho': round(rho, 3),
                                                     'p': round(p_rho, 3)},
           'fisher_local_vs_hosted_open': {'odds_ratio': round(odds, 3), 'p': round(p_fisher, 3)}}
    a.out.write_text(json.dumps(out, indent=2) + '\n')
    for g, title in GROUPS:
        x = groups[g]
        print(f"{title}: selector choice {x['selector_choice']}/{x['answers']}, cited chosen "
              f"{x['cited_chosen_config']}/{x['retrieval_citations']}, first half {x['cited_first_half']}/"
              f"{x['retrieval_citations']}, misstated {x['misstated']}/{x['claims']}")
    print(f"Spearman (log params vs misstated share, {len(open_rows)} open models): rho {rho:.3f}, p {p_rho:.3f}")
    print(f'Fisher local vs hosted open: odds ratio {odds:.3f}, p {p_fisher:.3f}')
    if a.tex:
        write_tex(rows, groups, a.tex)
        print(f'wrote {a.tex}')


if __name__ == '__main__':
    main()
