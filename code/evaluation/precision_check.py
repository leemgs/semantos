#!/usr/bin/env python3
"""Do the local-model findings depend on 4-bit quantization?

Compares the 4-bit GGUF runs of the main audit with higher-precision reruns
through the same model_audit.py pipeline (all input variants, cited and matched
uncited deletion): Llama-3.1-8B and Phi-4 with bf16 weights through OpenRouter
providers that declare bf16 (a different serving stack than llama.cpp), and
Qwen2.5-7B as an 8-bit (Q8_0) GGUF in llama.cpp, the highest precision that
fits this machine. Qwen2.5-14B has no full-precision endpoint and was not rerun.

For each pair it reports, per input variant, whether every seed's choice is the
same, the deletion outcomes, and the automatic explanation checks of
mitigation_baseline.py on the full-context answers.

    python3 precision_check.py --out results/model-audit-summary/precision.json [--tex ../../paper/precision.tex]
"""
import argparse
import collections
import json
from pathlib import Path

import mitigation_baseline as mb

HERE = Path(__file__).resolve().parent
RES = HERE/'results'
PAIRS = [('Qwen2.5-7B', 'model-audit-qwen2.5-7b', 'model-audit-q8-qwen2.5-7b', '8-bit (Q8\\_0)'),
         ('Llama-3.1-8B', 'model-audit-llama3.1-8b', 'model-audit-fp-llama3.1-8b', 'bf16'),
         ('Phi-4', 'model-audit-phi-4', 'model-audit-fp-phi-4', 'bf16')]
VARIANTS = ['full', 'no_graph', 'no_retrieval', 'model_only', 'delete_cited', 'delete_uncited']


def summarize(d):
    recs = json.loads((RES/d/'records.json').read_text())
    choices = collections.defaultdict(dict)
    for r in recs:
        if r['variant'] in VARIANTS and r.get('status') == 'valid':
            choices[r['variant']][r['seed']] = r['answer']['config']
    faith = [r for r in recs if r['variant'] == 'faithfulness']
    full = [r for r in recs if r['variant'] == 'full' and r.get('status') == 'valid']
    checks = mb.aggregate([mb.check(r['answer'], json.loads(r['prompt'])['evidence']) for r in full])
    invalid = sum(r.get('status') != 'valid' for r in recs if r['variant'] in VARIANTS)
    return {'choices': {v: choices[v] for v in VARIANTS if v in choices},
            'deletion_estimable': sum(r['status'] == 'valid' for r in faith),
            'cited_changed': sum(bool(r.get('cited_action_changed')) for r in faith),
            'uncited_changed': sum(bool(r.get('uncited_action_changed')) for r in faith),
            'full_checks': checks, 'invalid': invalid, 'plan_model': json.loads((RES/d/'plan.json').read_text())['model']}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--tex', type=Path)
    a = ap.parse_args()
    rows = []
    for name, low, high, prec in PAIRS:
        lo, hi = summarize(low), summarize(high)
        same = {}  # compared on the seeds valid in both runs
        for v in VARIANTS:
            if v in lo['choices'] and v in hi['choices']:
                common = set(lo['choices'][v]) & set(hi['choices'][v])
                same[v] = bool(common) and all(lo['choices'][v][s] == hi['choices'][v][s] for s in common)
        rows.append({'model': name, 'precision': prec.replace('\\', ''), 'four_bit': lo, 'higher': hi,
                     'same_choice_by_variant': same})
        print(f"{name} ({prec.replace(chr(92), '')}): same choice per variant {same}; deletion changed cited "
              f"{lo['cited_changed']}->{hi['cited_changed']}, uncited {lo['uncited_changed']}->{hi['uncited_changed']} "
              f"of {hi['deletion_estimable']} estimable; overstated {lo['full_checks']['overstated_explanations']}->"
              f"{hi['full_checks']['overstated_explanations']}; invalid {lo['invalid']}->{hi['invalid']}")
    a.out.write_text(json.dumps(rows, indent=2) + '\n')
    if a.tex:
        lines = [r'\begin{tabular}{@{}llrrrr@{}}', r'\toprule',
                 r'Model & Precision & Same choice & Del.\ cited & Del.\ unc. & Overst. \\', r'\midrule']
        for (name, _, _, prec), r in zip(PAIRS, rows):
            lo, hi = r['four_bit'], r['higher']
            same = r['same_choice_by_variant']
            est = hi['deletion_estimable']
            dc = f"{lo['cited_changed']}$\\to${hi['cited_changed']}/{est}" if est else 'n/e'
            du = f"{lo['uncited_changed']}$\\to${hi['uncited_changed']}/{est}" if est else 'n/e'
            lines.append(f"{name} & {prec} & {sum(same.values())}/{len(same)} & {dc} & {du} & "
                         f"{lo['full_checks']['overstated_explanations']}$\\to${hi['full_checks']['overstated_explanations']}/5 \\\\")
        lines += [r'\bottomrule', r'\end{tabular}']
        a.tex.write_text('\n'.join(lines) + '\n')
        print(f'wrote {a.tex}')


if __name__ == '__main__':
    main()
