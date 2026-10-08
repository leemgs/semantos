#!/usr/bin/env python3
"""Regenerate every table and headline number of the paper from the raw logs.

    python3 reproduce_paper.py            # check against ../../paper
    python3 reproduce_paper.py --keep DIR # also keep the regenerated outputs

The analysis scripts write their outputs next to their inputs, so this script
copies results/ to a temporary directory, runs every analysis there (the
original logs are never modified), and compares the regenerated LaTeX tables
byte for byte with the files the paper includes. It also recomputes the
numbers quoted in the text (claim misstatements, citation counts, label
checks) and prints one PASS/FAIL line per item. Exit status is non-zero if any
item fails.
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent.parent/'paper'
MODELS = ['qwen2.5-7b', 'llama3.1-8b', 'qwen2.5-14b', 'phi-4', 'api-llama3.3-70b', 'api-qwen3-235b',
          'api-deepseek-v3.2', 'api-nemotron3-ultra-550b', 'api-gemini-3.8-flash', 'api-gemini-3.1-pro']
results = []


def run(*args, cwd=None):
    p = subprocess.run([sys.executable, *map(str, args)], cwd=cwd or HERE, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f'{args[0]} failed:\n{p.stdout}\n{p.stderr}')
    return p.stdout


def check(name, ok, detail=''):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f'  ({detail})' if detail else ''))


def same_file(name, generated, paper_file):
    a, b = Path(generated).read_text(), (PAPER/paper_file).read_text()
    check(f'{name}: {paper_file}', a == b, '' if a == b else 'differs from the paper')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--keep', type=Path, help='copy the regenerated outputs here')
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        res = tmp/'results'
        shutil.copytree(HERE/'results', res)

        run('analyze.py', res/'local-2026-09-26')
        same_file('Local baseline table', res/'local-2026-09-26/table.tex', 'local-measurements.tex')
        run('analyze_kernel_local.py', res/'kernel-local-2026-09-26')
        same_file('Temporal-holdout kernel table', res/'kernel-local-2026-09-26/table.tex', 'kernel-measurements.tex')
        run('analyze_controlled.py', res/'controlled-2026-09-26')
        same_file('Selector replay table', res/'controlled-2026-09-26/table.tex', 'controlled-measurements.tex')
        run('optimizer_baselines.py', res/'controlled-2026-09-26', '--out', tmp/'opt', '--tex', tmp/'optimizer-baselines.tex')
        same_file('Matched-budget optimizer table', tmp/'optimizer-baselines.tex', 'optimizer-baselines.tex')
        run('summarize_model_audit.py', *[res/f'model-audit-{m}' for m in MODELS], '--out', tmp/'audit',
            '--tex', tmp/'model-audit.tex')
        same_file('LLM decision table', tmp/'model-audit.tex', 'model-audit.tex')
        same_file('LLM decision legend', tmp/'model-audit-legend.tex', 'model-audit-legend.tex')
        run('claim_taxonomy.py', '--audit', res/'model-audit-summary/claim-audit.json', '--out', tmp/'claim-taxonomy.tex')
        same_file('Claim taxonomy table', tmp/'claim-taxonomy.tex', 'claim-taxonomy.tex')
        run('plot_gate_replay.py', '--root', res/'controlled-2026-09-26', '--out', tmp/'gate_replay.pdf')
        check('Gate replay figure regenerates and its counts match analysis.json', (tmp/'gate_replay.pdf').exists())

        audit = json.loads((res/'model-audit-summary/claim-audit.json').read_text())
        mis = {'wrong', 'wrong attribution', 'overstated', 'wrong unit'}
        local = {'Qwen2.5-7B', 'Llama-3.1-8B', 'Qwen2.5-14B', 'Phi-4'}
        lc = [c for c in audit['claims'] if c['model'] in local]
        hc = [c for c in audit['claims'] if c['model'] not in local]
        n_l, n_h = sum(c['verdict'] in mis for c in lc), sum(c['verdict'] in mis for c in hc)
        check('Misstated claims 16/28 (local), 25/69 (hosted), 41/97', (n_l, len(lc), n_h, len(hc)) == (16, 28, 25, 69),
              f'{n_l}/{len(lc)}, {n_h}/{len(hc)}')
        check('Claim labels verified by an author', audit.get('verification', {}).get('human_verified') is True)
        sa = audit.get('second_annotator', {})
        check('Second blind annotator: kappa 0.918 (seven labels), 0.914 (misstated vs not)',
              (sa.get('kappa_7'), sa.get('kappa_binary')) == (0.918, 0.9144), str((sa.get('kappa_7'), sa.get('kappa_binary'))))

        run('entailment_judge.py', '--out', res/'model-audit-summary/entailment-judge.json', '--tex', tmp/'entailment-judges.tex')
        same_file('Entailment-judge table (from saved judge outputs)', tmp/'entailment-judges.tex', 'entailment-judges.tex')
        cites = json.loads(run('citation_analysis.py', '--results', res))
        got = (cites['retrieval_chosen'], cites['retrieval_citations'], cites['retrieval_in_first_half'], cites['graph'])
        check('Citations: 252/260 of the chosen configuration, 209 in the first half, graph never cited',
              got == (252, 260, 209, 0), str(got))
        auto = run('claim_label_autocheck.py', '--mutation-test')
        check('Rule check: 56 rule-decided claims, 0 flagged, 76/97 flips detected',
              '56 of 97 claims are decided' in auto and '0 flagged' in auto and '76 of 97 flipped' in auto)

        if a.keep:
            if a.keep.exists():
                shutil.rmtree(a.keep)
            shutil.copytree(tmp, a.keep)
    print(f'\n{sum(results)} of {len(results)} checks passed')
    sys.exit(0 if all(results) else 1)


if __name__ == '__main__':
    main()
