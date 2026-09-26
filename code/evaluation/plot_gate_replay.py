"""Plot the frozen-gate replay on held-out test runs from the raw controlled log.

Every point is one measured test run: its observed deadline-miss fraction and the
decision the frozen gate made from the configuration's training score. The counts
drawn in the figure are recomputed here and checked against analysis.json.
"""
import argparse
import json
from pathlib import Path
import random

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from analyze_controlled import analyze
from controlled_kernel import misses

ACCEPT = '#2a78d6'   # categorical slot 1 (validated palette, light surface)
VETO = '#eb6834'     # categorical slot 2
INK, MUTED = '#0b0b0b', '#52514e'
ORDER = ['s50000_aall', 's50000_aone', 's1000000_aall', 's1000000_aone']
LABELS = ['50µs\nall CPUs', '50µs\none CPU', '1ms\nall CPUs', '1ms\none CPU']


def gate_points(root):
    plan = json.loads((root / 'plan.json').read_text())
    frozen = json.loads((root / 'frozen.json').read_text())
    tau = json.loads((root / 'gate.json').read_text())['thresholds']['0.05']
    runs = [json.loads(s) for s in (root / 'runs.jsonl').read_text().splitlines()]
    points = {}
    for r in runs:
        if r['role'] != 'test':
            continue
        frac = misses(r['events'], plan['deadline_ns']) / len(r['events'])
        points.setdefault(r['period_ns'] // 1000000, []).append(
            (r['name'], frac, frozen['score'][r['name']] < tau, frac > plan['unsafe_fraction']))
    return points, tau, plan['unsafe_fraction']


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, default=Path(__file__).parent / 'results/controlled-2026-09-26')
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    analyze(a.root)  # hash, lineage and freeze checks; raises on any mismatch
    points, tau, unsafe = gate_points(a.root)
    reported = {(s['period_ms'], s['alpha']): s['counts']
                for s in json.loads((a.root / 'analysis.json').read_text())['safety_replay']}

    plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Nimbus Roman', 'DejaVu Serif'],
                         'font.size': 7, 'pdf.fonttype': 42, 'mathtext.fontset': 'stix', 'axes.edgecolor': MUTED,
                         'axes.labelcolor': INK, 'xtick.color': MUTED, 'ytick.color': MUTED})
    fig, axes = plt.subplots(1, 2, figsize=(3.3, 1.9), sharey=True)
    rng = random.Random(4088)
    for ax, period in zip(axes, sorted(points)):
        pts = points[period]
        fn = sum(acc and bad for _, _, acc, bad in pts)
        n_unsafe = sum(bad for *_, bad in pts)
        c = reported[(period, 0.05)]
        if (fn, n_unsafe - fn) != (c['fn'], c['tp']):
            raise ValueError('figure counts disagree with analysis.json')
        for name, frac, acc, _ in pts:
            x = ORDER.index(name) + rng.uniform(-0.18, 0.18)
            ax.scatter(x, frac, s=14, marker='o' if acc else '^', color=ACCEPT if acc else VETO,
                       edgecolors='white', linewidths=0.6, zorder=3)
        ax.axhline(unsafe, color=MUTED, lw=0.8, ls=(0, (3, 2)), zorder=1)
        ax.set_title(f'{period} ms test period', fontsize=7, color=INK, pad=3)
        ax.text(0.03, 0.80, f'accepted & unsafe:\n{fn} of {n_unsafe} unsafe runs', transform=ax.transAxes,
                va='top', ha='left', fontsize=6.5, color=INK)
        ax.set_xticks(range(4), LABELS, fontsize=5.8)
        ax.set_xlim(-0.5, 3.5)
        ax.set_ylim(-0.03, 1.03)
        ax.grid(axis='y', color='#e4e3df', lw=0.5, zorder=0)
        for side in ('top', 'right'):
            ax.spines[side].set_visible(False)
        ax.tick_params(length=2, width=0.5)
    axes[0].set_ylabel('Deadline-miss fraction per run')
    axes[1].text(3.5, unsafe + 0.02, 'unsafe label (>10%)', ha='right', va='bottom', fontsize=5.8, color=MUTED)
    handles = [plt.Line2D([], [], marker='o', ls='', color=ACCEPT, markeredgecolor='white', label=f'accepted ($u<\\tau={tau}$)'),
               plt.Line2D([], [], marker='^', ls='', color=VETO, markeredgecolor='white', label='vetoed')]
    fig.legend(handles=handles, loc='lower center', ncol=2, frameon=False, fontsize=6.5,
               bbox_to_anchor=(0.55, -0.01), handletextpad=0.2, columnspacing=1.2)
    fig.tight_layout(rect=(0, 0.07, 1, 1), w_pad=0.6)
    fig.savefig(a.out)
    print(json.dumps({'out': str(a.out), 'tau': tau,
                      'fn_over_unsafe': {k: f"{reported[(k, 0.05)]['fn']}/{reported[(k, 0.05)]['fn'] + reported[(k, 0.05)]['tp']}" for k in sorted(points)}}))


if __name__ == '__main__':
    main()
