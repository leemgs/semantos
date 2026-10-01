"""Matched-budget BO and RL baselines on the controlled follow-up, by offline replay.

Each method may evaluate B training-period runs (2 ms). Evaluating configuration c
returns the P95 lateness of one recorded training run of c, drawn uniformly with
replacement from its ten measured runs; nothing is simulated beyond this bootstrap.
After B evaluations the method recommends one configuration, which is scored by the
same paired held-out replay as the non-LLM selectors and the model audit. Test
outcomes are read only after every recommendation is fixed. B=40 equals the forty
training runs given to the table selector (and summarized for the LLMs).

Methods (all start by evaluating each configuration once, in random order):
  random    uniform evaluations; recommend the lowest observed mean
  egreedy   RL: tabular one-step Q learning with sample-average values, epsilon=0.1
  ucb1      RL: UCB1 on reward 1 - min(p95, 2000 us)/2000 us
  gp_ei     BO: Gaussian process on (log10 slack, all CPUs) with fixed RBF kernel on
            standardized log P95, expected improvement; recommend the lowest
            posterior mean
"""
import argparse
import json
import math
from pathlib import Path
import random
import statistics
import time

import numpy as np

from controlled_kernel import digest, quantile, write
from model_audit import heldout

BUDGETS = [4, 8, 16, 40]
METHODS = ['random', 'egreedy', 'ucb1', 'gp_ei']
REPLICATES = 1000
EPSILON = 0.1
GP = {'lengthscale': 1.0, 'signal_var': 1.0, 'noise_var': 0.1}


def training_pool(root):
    plan = json.loads((root/'plan.json').read_text())
    rows = [json.loads(line) for line in (root/'runs.jsonl').read_text().splitlines()]
    pool = {c['name']: [quantile(r['events']) for r in rows if r['role'] == 'train' and r['name'] == c['name']]
            for c in plan['configs']}
    features = {c['name']: (math.log10(c['slack_ns']), 1.0 if len(c['cpus']) > 1 else 0.0) for c in plan['configs']}
    return plan, pool, features


def gp_posterior(xs, ys, xq):
    """Posterior mean and sd at xq for a zero-mean GP on standardized ys."""
    X, Q = np.array(xs), np.array(xq)
    y = np.array(ys)
    mu, sd = y.mean(), y.std() or 1.0
    z = (y-mu)/sd

    def k(a, b):
        d2 = ((a[:, None, :]-b[None, :, :])**2).sum(-1)
        return GP['signal_var']*np.exp(-0.5*d2/GP['lengthscale']**2)
    K = k(X, X)+GP['noise_var']*np.eye(len(X))
    Ks = k(Q, X)
    alpha = np.linalg.solve(K, z)
    mean = Ks@alpha
    var = GP['signal_var']-np.einsum('ij,ji->i', Ks, np.linalg.solve(K, Ks.T))
    return mean*sd+mu, np.sqrt(np.maximum(var, 1e-12))*sd


def run(method, budget, pool, features, rng):
    names = list(pool)
    pulls = []  # (config, p95)

    def pull(c):
        pulls.append((c, rng.choice(pool[c])))
    for c in rng.sample(names, len(names)):
        if len(pulls) < budget:
            pull(c)
    while len(pulls) < budget:
        obs = {c: [p for n, p in pulls if n == c] for c in names}
        if method == 'random':
            pull(rng.choice(names))
        elif method == 'egreedy':
            if rng.random() < EPSILON:
                pull(rng.choice(names))
            else:
                pull(min(names, key=lambda c: (statistics.mean(obs[c]), rng.random())))
        elif method == 'ucb1':
            t = len(pulls)
            reward = {c: statistics.mean(1-min(p, 2000.0)/2000.0 for p in obs[c]) for c in names}
            pull(max(names, key=lambda c: reward[c]+math.sqrt(2*math.log(t)/len(obs[c]))))
        elif method == 'gp_ei':
            xs = [features[c] for c, _ in pulls]
            ys = [math.log(p) for _, p in pulls]
            mean, sd = gp_posterior(xs, ys, [features[c] for c in names])
            best = min(ys)
            zz = (best-mean)/sd
            ei = (best-mean)*np.vectorize(lambda v: 0.5*(1+math.erf(v/math.sqrt(2))))(zz) \
                + sd*np.exp(-0.5*zz**2)/math.sqrt(2*math.pi)
            pull(names[int(np.argmax(ei))])
    obs = {c: [p for n, p in pulls if n == c] for c in names}
    if method == 'gp_ei':
        mean, _ = gp_posterior([features[c] for c, _ in pulls], [math.log(p) for _, p in pulls],
                               [features[c] for c in names])
        choice = names[int(np.argmin(mean))]
    else:
        choice = min((c for c in names if obs[c]), key=lambda c: statistics.mean(obs[c]))
    return {'choice': choice, 'pulls': {c: len(obs[c]) for c in names}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--tex', type=Path, help='write the paper table here')
    args = p.parse_args()
    if args.out.exists():
        p.error('choose a new output directory')
    args.out.mkdir(parents=True)
    plan, pool, features = training_pool(args.root)
    write(args.out/'plan.json', {
        'budgets': BUDGETS, 'methods': METHODS, 'replicates': REPLICATES, 'seed_base': 4088,
        'epsilon': EPSILON, 'gp': GP, 'ucb_reward': '1 - min(p95, 2000 us)/2000 us',
        'environment': 'bootstrap draw of one recorded 2 ms training run of the chosen config',
        'recommendation': 'lowest observed mean (gp_ei: lowest posterior mean)',
        'scoring': 'model_audit.heldout paired replay on the 5 and 8 ms test grid, after all runs',
        'input_hashes_sha256': digest(args.root/'SHA256SUMS.json'), 'source_sha256': digest(__file__),
        'frozen_utc_ns': time.time_ns()})
    runs = []
    for method in METHODS:
        for budget in BUDGETS:
            for r in range(REPLICATES):
                rng = random.Random(f'{method}-{budget}-{4088+r}')
                runs.append({'method': method, 'budget': budget, 'replicate': r,
                             **run(method, budget, pool, features, rng)})
    write(args.out/'runs.json', runs)
    # Held-out outcomes are read only now, once per configuration.
    table = {(h['config'], h['period_ms']): h for h in heldout(
        args.root, [{'status': 'valid', 'variant': 'config', 'seed': 0, 'answer': {'config': c}} for c in pool])}
    control = plan['configs'][0]['name']
    bad = [c['name'] for c in plan['configs'] if c['slack_ns'] >= 1000000]
    summary = []
    for method in METHODS:
        for budget in BUDGETS:
            sel = [x for x in runs if x['method'] == method and x['budget'] == budget]
            counts = {c: sum(x['choice'] == c for x in sel) for c in pool}
            row = {'method': method, 'budget': budget, 'replicates': len(sel), 'choices': counts,
                   'control_fraction': counts[control]/len(sel),
                   'mean_pulls_1ms_configs': statistics.mean(sum(x['pulls'][c] for c in bad) for x in sel)}
            for ms in (5, 8):
                row[f'expected_paired_change_pct_{ms}ms'] = statistics.mean(
                    table[x['choice'], ms]['reduction_pct']['mean'] for x in sel)
            summary.append(row)
    write(args.out/'summary.json', summary)
    lines = ['# Matched-budget BO/RL baselines (offline replay)', '',
             'Each method evaluates B recorded 2 ms training runs (bootstrap) and recommends one '
             'configuration, scored by the paired held-out replay used for all other selectors.', '',
             '| Method | B | Control chosen | Expected paired change 5/8 ms (%) | Mean evaluations of 1 ms configs |',
             '|---|---|---|---|---|']
    for row in summary:
        lines.append(f"| {row['method']} | {row['budget']} | {row['control_fraction']:.1%} | "
                     f"{row['expected_paired_change_pct_5ms']:.1f} / {row['expected_paired_change_pct_8ms']:.1f} | "
                     f"{row['mean_pulls_1ms_configs']:.2f} |")
    (args.out/'summary.md').write_text('\n'.join(lines)+'\n')
    if args.tex:
        label = {'random': 'Random search', 'egreedy': '$\\epsilon$-greedy (RL)', 'ucb1': 'UCB1 (RL)',
                 'gp_ei': 'GP-EI (BO)'}
        body = []
        for method in METHODS:
            rows = {r['budget']: r for r in summary if r['method'] == method}
            cells = [f"{100*rows[b]['control_fraction']:.0f}\\,/\\,${rows[b]['expected_paired_change_pct_5ms']:.0f}$"
                     for b in BUDGETS]
            body.append(' & '.join([label[method]] + cells + [f"{rows[BUDGETS[-1]]['mean_pulls_1ms_configs']:.1f}"]) + ' \\\\')
        args.tex.write_text('\\begin{tabular}{@{}l' + 'c'*len(BUDGETS) + 'c@{}}\n\\toprule\n'
                            + ' & '.join(['Method'] + [f'$B={b}$' for b in BUDGETS] + ['1\\,ms evals']) + ' \\\\\n\\midrule\n'
                            + '\n'.join(body) + '\n\\bottomrule\n\\end{tabular}\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
