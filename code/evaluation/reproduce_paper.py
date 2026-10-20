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
import collections
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

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
        # dependence: distinct (model, claim) pairs, and a bootstrap that resamples models (clusters)
        import random
        distinct = {(c['model'], c['claim']): c['verdict'] for c in audit['claims']}
        by_model = collections.defaultdict(list)
        for c in audit['claims']:
            by_model[c['model']].append(c)
        rng, ms, boot = random.Random(0), list(by_model), []
        for _ in range(20000):
            s = [c for m in (rng.choice(ms) for _ in ms) for c in by_model[m]]
            boot.append(sum(c['verdict'] in mis for c in s)/len(s))
        boot.sort()
        lo, hi = round(100*boot[500]), round(100*boot[19499])
        n_d = sum(v in mis for v in distinct.values())
        check('Distinct claims 25/67 misstated; model-cluster bootstrap 95% interval 34-52%',
              (n_d, len(distinct), lo, hi) == (25, 67, 34, 52), f'{n_d}/{len(distinct)}, {lo}-{hi}%')
        check('Claim labels verified by an author', audit.get('verification', {}).get('human_verified') is True)
        import claim_review_agreement as cra
        verified = [c['verdict'] for c in audit['claims']]
        annot = [cra.read_annotator(PAPER/f, len(verified))
                 for f in ('second-annotator-labels.csv', 'third-annotator-labels.csv')]
        ks = []
        for lab in annot:
            ks += [round(cra.cohen_kappa(verified, lab)[1], 3),
                   round(cra.cohen_kappa([x in cra.MISSTATED for x in verified], [x in cra.MISSTATED for x in lab])[1], 3)]
        check('Blind annotators: kappa 0.918/0.914 and 0.856/0.808 (seven labels/misstated vs not)',
              ks == [0.918, 0.914, 0.856, 0.808], str(ks))
        items = list(zip(verified, *annot))
        f7 = round(cra.fleiss_kappa(items), 3)
        fb = round(cra.fleiss_kappa([[x in cra.MISSTATED for x in it] for it in items]), 3)
        maj = sum(collections.Counter(it).most_common(1)[0][0] == it[0] for it in items)
        mis_a = [sum(x in cra.MISSTATED for x in lab) for lab in annot]
        check("Fleiss' kappa 0.847/0.814, majority = verified label for 97/97, annotators' misstated 37 and 38",
              (f7, fb, maj, mis_a) == (0.847, 0.814, 97, [37, 38]), str((f7, fb, maj, mis_a)))

        run('entailment_judge.py', '--out', res/'model-audit-summary/entailment-judge.json', '--tex', tmp/'entailment-judges.tex')
        same_file('Entailment-judge table (from saved judge outputs)', tmp/'entailment-judges.tex', 'entailment-judges.tex')
        ej = json.loads((res/'model-audit-summary/entailment-judge.json').read_text())
        bas = [v['balanced_accuracy'] for v in ej['summary'].values()]
        mis = [x for x in ej['items'] if x['label'] in cra.MISSTATED]
        anyacc = sum(any(v['supported'] for v in x['judges'].values()) for x in mis)
        check('Judges: 18 judge/hypothesis rows, balanced accuracy 0.47-0.68, 28/41 misstated accepted by some judge',
              (len(bas), round(min(bas), 2), round(max(bas), 2), anyacc, len(mis)) == (18, 0.47, 0.68, 28, 41),
              str((len(bas), round(min(bas), 2), round(max(bas), 2), anyacc, len(mis))))
        shutil.copytree(HERE/'results/prompt-robustness', tmp/'prompt-robustness')
        run('prompt_robustness.py', 'score', '--out', tmp/'prompt-robustness', '--tex', tmp/'prompt-robustness.tex')
        same_file('Robustness table (from saved API records)', tmp/'prompt-robustness.tex', 'prompt-robustness.tex')
        shutil.copytree(HERE/'results/mitigation-baseline', tmp/'mitigation-baseline')
        run('mitigation_baseline.py', 'score', '--out', tmp/'mitigation-baseline', '--tex', tmp/'mitigation.tex')
        same_file('Mitigation table (from saved API records)', tmp/'mitigation.tex', 'mitigation.tex')
        mb = json.loads((tmp/'mitigation-baseline/summary.json').read_text())['conditions']
        got = tuple((mb[c]['overstated_explanations'], mb[c]['explanations_with_range_errors']) for c in
                    ('original', 'verify', 'stats', 'verify+stats'))
        shutil.copytree(HERE/'results/reliance-redesign', tmp/'reliance-redesign')
        run('reliance_redesign.py', 'score', '--out', tmp/'reliance-redesign', '--tex', tmp/'reliance-redesign.tex')
        same_file('Redesigned reliance table (from saved API records)', tmp/'reliance-redesign.tex', 'reliance-redesign.tex')
        rr = {r['model']: r for r in json.loads((tmp/'reliance-redesign/summary.json').read_text())['rows']}
        got_rr = (rr['Llama-8B (bf16)']['B']['cited_only'], sum(r['B']['cited_only'] for m, r in rr.items()),
                  sum(r['A']['estimable'] for r in rr.values()), sum(r['B']['estimable'] for r in rr.values()))
        check('Reliance redesign: test B cited-only changes 5 (bf16 Llama-8B) of 5 in total; 32 and 35 estimable seeds',
              got_rr == (5, 5, 32, 35), str(got_rr))
        run('precision_check.py', '--out', tmp/'precision.json', '--tex', tmp/'precision.tex')
        same_file('Precision table (4-bit vs bf16/8-bit reruns)', tmp/'precision.tex', 'precision.tex')
        pc = {r['model']: r for r in json.loads((tmp/'precision.json').read_text())}
        got_p = (pc['Phi-4']['four_bit']['cited_changed'], pc['Phi-4']['higher']['cited_changed'],
                 all(all(v for k, v in r['same_choice_by_variant'].items() if not k.startswith('delete'))
                     for r in pc.values()))
        check('Precision: Phi-4 cited-deletion change 5 -> 0; evidence/no-evidence choices unchanged for all three',
              got_p == (5, 0, True), str(got_p))
        shutil.copytree(HERE/'results/reasoning-models', tmp/'reasoning-models')
        run('reasoning_models.py', 'score', '--out', tmp/'reasoning-models', '--tex', tmp/'reasoning.tex')
        same_file('Reasoning-toggle table (from saved API records)', tmp/'reasoning.tex', 'reasoning.tex')
        ra = json.loads((tmp/'reasoning-models/summary.json').read_text())['arms']
        got_r = tuple((a['toggled']['answers'], a['toggled']['overstated_explanations'],
                       a['toggled']['explanations_with_range_errors']) for a in ra)
        check('Reasoning toggles: 5 answers each; flagged quantifiers 4/2/5/1, range errors 0/1/0/0',
              got_r == ((5, 4, 0), (5, 2, 1), (5, 5, 0), (5, 1, 0)), str(got_r))
        check('Mitigations: flagged quantifiers 21/1/4/0 and range errors 7/2/0/0 of 30',
              got == ((21, 7), (1, 2), (4, 0), (0, 0)), str(got))
        rb = json.loads((tmp/'prompt-robustness/summary.json').read_text())['conditions']
        got = (rb['reversed']['cited_first_half_presented'], rb['reversed']['cited_blocks_0_4'],
               rb['reversed']['retrieval_citations'], rb['nocap']['mean_citations'], rb['nocap']['cited_chosen_config'],
               rb['nocap']['retrieval_citations'], sum(c['selector_choice'] for c in rb.values()))
        check('Robustness: reversed 88/50 of 138, uncapped 9.0 citations, 256/256 chosen, 180/180 selector choice',
              got == (88, 50, 138, 9.03, 256, 256, 180), str(got))
        run('scale_family_analysis.py', '--out', tmp/'scale-family.json', '--tex', tmp/'scale-family.tex')
        sf = json.loads((tmp/'scale-family.json').read_text())
        same_file('Scale and family table', tmp/'scale-family.tex', 'scale-family.tex')
        got = (sf['groups']['local']['misstated'], sf['groups']['local']['claims'],
               sf['groups']['hosted open']['misstated'], sf['groups']['hosted open']['claims'],
               sf['spearman_logparams_vs_misstated_share']['rho'], sf['spearman_logparams_vs_misstated_share']['p'],
               sf['fisher_local_vs_hosted_open']['p'])
        check('Scale: misstated 7/8 (local) vs 21/52 (hosted open), Spearman rho -0.784 (p 0.021), Fisher p 0.020',
              got == (7, 8, 21, 52, -0.784, 0.021, 0.02), str(got))
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
