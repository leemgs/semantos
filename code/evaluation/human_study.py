#!/usr/bin/env python3
"""Materials and analysis for a human-impact study prepared for pre-registration (not yet run).

Question: does a misstated rationale attached to a correct, cited decision
change what a reader believes the evidence shows? Each participant sees the
frozen evidence of the main audit (training table and 40 retrieval runs,
behind a click that is logged) and one advisor brief: the decision
(s50000_aall) and its citations, plus one of three rationales, between
subjects:

* M  the model's verbatim explanation, which misstates the evidence
     (errors verified in claim-audit.json and re-checked here against the
     evidence);
* C  the same text with only the misstated phrases minimally corrected
     (AI-drafted; an author must verify each before data collection);
* N  no rationale (decision and citations only).

The brief is drawn from six source explanations (stimulus sampling). Every
participant then answers the same six yes/no probes about the evidence; the
probes a source explanation misstates are its targeted probes. Primary
outcome: per-participant accuracy on targeted probes, M versus C.

    python3 human_study.py build --out ../../paper/human-study     # stimuli.json, instrument.html, online.html
    python3 human_study.py power [--sims 2000]                     # simulated power under stated assumptions
    python3 human_study.py analyze --responses responses.csv [--out summary.json]

No responses exist yet; `power` simulates data only to size the study and
its output must never be reported as human data.
"""
import argparse
import csv
import hashlib
import json
import random
import statistics
from pathlib import Path

import model_audit

HERE = Path(__file__).resolve().parent
RES = HERE/'results'
ROOT = RES/'controlled-2026-09-26'
CONDITIONS = ['M', 'C', 'N']
STIMULUS_MODELS = 3  # consecutive participants cycle stimuli within condition

# Probes: id, question, function of the evidence giving the correct answer.
PROBES = [
    ('P1', 'Is the highest P95 among the s50000_aone retrieval runs above 500 us?',
     lambda ev: max(ev['runs']['s50000_aone']) > 500),
    ('P2', 'Does any run of a configuration other than s50000_aall have a P95 below the highest s50000_aall run?',
     lambda ev: any(v < max(ev['runs']['s50000_aall']) for c, vs in ev['runs'].items() if c != 's50000_aall' for v in vs)),
    ('P3', 'Is every s1000000 run (both s1000000 configurations) above 800 us?',
     lambda ev: all(v > 800 for c, vs in ev['runs'].items() if c.startswith('s1000000') for v in vs)),
    ('P4', 'Is the highest P95 among the s50000_aall retrieval runs above 150 us?',
     lambda ev: max(ev['runs']['s50000_aall']) > 150),
    ('P5', 'Does s50000_aall have the lowest P95 in every one of the ten retrieval blocks?',
     lambda ev: ev['block_wins'].get('s50000_aall', 0) == ev['blocks']),
    ('P6', 'Does the evidence report a statistical significance test between configurations?',
     lambda ev: False),  # the evidence holds only measurements, no test statistics
]

# Source explanations: model directory, seed, misstated phrases (must occur
# verbatim in the stored explanation) with their minimal corrections, targeted
# probes, and where to cut a truncated explanation (last full sentence).
STIMULI = [
    {'id': 'S1', 'dir': 'api-nemotron3-ultra-550b', 'seed': 4089, 'targets': ['P1', 'P5'],
     'cut': 'consistently exceed 748 microseconds.',
     'edits': [('consistently achieves the lowest periodic wake-up P95 latency across all retrieval runs',
                'achieves the lowest periodic wake-up P95 latency in 8 of the 10 retrieval blocks'),
               ('(85.0 to 430.7 microseconds)', '(85.0 to 571.8 microseconds)')]},
    {'id': 'S2', 'dir': 'api-deepseek-v3.2', 'seed': 4089, 'targets': ['P2'], 'cut': None,
     'edits': [('which is lower than the lowest P95 observed for any other config (e.g., s50000_aone has runs up to 571.84 µs, '
                'and s1000000 configs are all above 748 µs)',
                'which is lower than every run of the two s1000000 configs (all above 748 µs), although some s50000_aone '
                'runs are lower (down to 85.033 µs) and others reach 571.84 µs')]},
    {'id': 'S3', 'dir': 'api-deepseek-v3.2', 'seed': 4088, 'targets': ['P3', 'P5'], 'cut': None,
     'edits': [('consistently shows the lowest P95 latencies across multiple trials',
                'shows the lowest P95 latency in 8 of the 10 retrieval blocks'),
               ('both s1000000 configurations are consistently above 800 μs',
                'both s1000000 configurations are above 748 μs in every run')]},
    {'id': 'S4', 'dir': 'api-llama3.3-70b', 'seed': 4089, 'targets': ['P4'], 'cut': None,
     'edits': [('with values ranging from 82.488 to 140.554', 'with values ranging from 82.488 to 183.217')]},
    {'id': 'S5', 'dir': 'api-qwen3-235b', 'seed': 4088, 'targets': ['P5', 'P6'],
     'cut': 'with the highest observed P95 being 183.217 us.',
     'append_m': " In contrast, all other configurations (including 's50000_aone', 's1000000_aall', and "
                 "'s1000000_aone') exhibit significantly higher P95 latency.",
     'append_c': " In contrast, the other configurations have higher mean P95 latency (227.4, 953.1 and 1014.0 us versus "
                 "110.5 us), although some s50000_aone runs are lower than some s50000_aall runs; the evidence "
                 "contains no significance test.",
     'edits': [("consistently shows the lowest P95 latency across multiple retrieval runs",
                "shows the lowest P95 latency in 8 of the 10 retrieval blocks")]},
    {'id': 'S6', 'dir': 'api-gemini-3.1-pro', 'seed': 4090, 'targets': ['P5'], 'cut': None,
     'edits': [('consistently achieves the lowest P95 latency', 'achieves the lowest P95 latency in 8 of the 10 retrieval blocks')]},
]


def evidence():
    _, items = model_audit.evidence(ROOT)
    runs, blocks = {}, {}
    for i in items:
        if i['kind'] == 'retrieval':
            runs.setdefault(i['config'], []).append(i['p95_us'])
            blocks.setdefault(i['id'].split('-')[2], {})[i['config']] = i['p95_us']
    wins = {}
    for b in blocks.values():
        c = min(b, key=b.get)
        wins[c] = wins.get(c, 0) + 1
    table = next(i for i in items if i['id'] == 'training-table')['values']
    return items, {'runs': runs, 'block_wins': wins, 'blocks': len(blocks), 'table': table}


def build(args):
    items, ev = evidence()
    keys = {pid: bool(f(ev)) for pid, _, f in PROBES}
    stimuli = []
    for s in STIMULI:
        rec = next(r for r in json.loads((RES/f"model-audit-{s['dir']}"/'records.json').read_text())
                   if r['variant'] == 'full' and r.get('status') == 'valid' and r['seed'] == s['seed'])
        text = rec['answer']['explanation']
        if s['cut']:
            assert s['cut'] in text, (s['id'], 'cut')
            text = text[:text.index(s['cut']) + len(s['cut'])]
        m, c = text, text
        for old, new in s['edits']:
            assert m.count(old) == 1, (s['id'], old)
            c = c.replace(old, new)
        m += s.get('append_m', '')
        c += s.get('append_c', '')
        stimuli.append({'id': s['id'], 'source_model_dir': s['dir'], 'seed': s['seed'], 'config': rec['answer']['config'],
                        'cited_ids': rec['answer']['cited_ids'], 'targets': s['targets'],
                        'M': m, 'C': c, 'C_status': 'AI-drafted correction; author verification required',
                        'M_note': ('verbatim' if not s['cut'] else 'verbatim up to the last complete sentence (the stored '
                                   'explanation is truncated)') + ('; its cut final sentence is completed' if 'append_m' in s else ''),
                        'source_explanation_sha256': hashlib.sha256(rec['answer']['explanation'].encode()).hexdigest()})
        print(s['id'], s['dir'], s['seed'], 'targets', s['targets'])
    out = {'design': 'between subjects: condition (M, C, N) x stimulus (S1-S6), one brief per participant',
           'probes': [{'id': p, 'question': q, 'answer': 'yes' if keys[p] else 'no'} for p, q, _ in PROBES],
           'evidence_facts': {'block_wins': ev['block_wins'], 'blocks': ev['blocks'],
                              'min_max': {c: [min(v), max(v)] for c, v in ev['runs'].items()}},
           'stimuli': stimuli,
           'assignment': 'participant k (0-based): condition CONDITIONS[k % 3], stimulus STIMULI[(k // 3) % 6]'}
    for st in stimuli:  # each stimulus misstates its targets: under M the stated facts imply the wrong answer
        assert st['targets'] and all(t in keys for t in st['targets'])
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out/'stimuli.json').write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n')
    page = INSTRUMENT.replace('/*DATA*/null', json.dumps({'stimuli': stimuli, 'probes': out['probes'],
                                                          'evidence': [i for i in items if i['kind'] != 'graph']},
                                                         ensure_ascii=False))
    (args.out/'instrument.html').write_text(page)
    data = {'stimuli': stimuli, 'probes': out['probes'], 'evidence': [i for i in items if i['kind'] != 'graph']}
    data['version'] = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:12]
    online = (args.out/'online-template.html').read_text().replace('/*DATA*/null', json.dumps(data, ensure_ascii=False))
    (args.out/'online.html').write_text(online)  # claude.ai artifact page; responses go to its db (see protocol)
    print('probe keys', {p: k for p, k in keys.items()})
    print(f"wrote {args.out/'stimuli.json'}, {args.out/'instrument.html'} and {args.out/'online.html'}")


def assign(k):
    return CONDITIONS[k % 3], STIMULI[(k // 3) % len(STIMULI)]['id']


def perm_test(rows, a='M', b='C', n=20000, seed=0):
    """One-sided stratified permutation test: mean targeted accuracy a < b, labels permuted within stimulus."""
    rows = [r for r in rows if r['condition'] in (a, b)]
    by = {}
    for r in rows:
        by.setdefault(r['stimulus'], []).append(r)

    def diff(lab):
        xa = [r['acc'] for r, l in zip(rows, lab) if l == a]
        xb = [r['acc'] for r, l in zip(rows, lab) if l == b]
        return statistics.mean(xa) - statistics.mean(xb) if xa and xb else 0.0
    obs = diff([r['condition'] for r in rows])
    rng = random.Random(seed)
    hits = 0
    for _ in range(n):
        lab = {}
        for g in by.values():
            ls = [r['condition'] for r in g]
            rng.shuffle(ls)
            lab.update({id(r): l for r, l in zip(g, ls)})
        hits += diff([lab[id(r)] for r in rows]) <= obs
    return obs, (hits + 1)/(n + 1)


def simulate(n_per_arm, p_ok=0.8, p_m=0.55, sd=1.0, rng=None):
    """Simulated participants (power analysis only): logit-normal participant ability."""
    import math
    lg = lambda p: math.log(p/(1 - p))
    rows = []
    for k in range(3*n_per_arm):
        cond, stim = assign(k)
        u = rng.gauss(0, sd)
        n_t = len(next(s for s in STIMULI if s['id'] == stim)['targets'])
        p = 1/(1 + math.exp(-(lg(p_m if cond == 'M' else p_ok) + u)))
        rows.append({'condition': cond, 'stimulus': stim, 'acc': sum(rng.random() < p for _ in range(n_t))/n_t})
    return rows


def power(args):
    rng = random.Random(1)
    print(f'assumptions: P(correct targeted) = {args.p_ok} under C/N and {args.p_m} under M; '
          f'participant SD {args.sd} (logit); one-sided alpha .05; simulated data, not human data')
    res = {}
    for n in args.n:
        sig = sum(perm_test(simulate(n, args.p_ok, args.p_m, args.sd, rng), n=199, seed=i)[1] < 0.05
                  for i in range(args.sims))
        res[n] = sig/args.sims
        print(f'n per arm {n:3d} (total {3*n}): power {res[n]:.2f}')
    return res


def keep(r, seen):
    """Pre-registered exclusions: failed attention item, incomplete, under 60 s, duplicate code (first kept)."""
    ok = (r.get('attention', '').strip().lower() == 'pass' and all(r.get(p, '').strip() for p, _, _ in PROBES)
          and r.get('trust', '').strip() and float(r.get('seconds') or 0) >= 60 and r['participant'] not in seen)
    seen.add(r['participant'])
    return ok


def analyze(args):
    """responses.csv: participant, condition, stimulus, P1..P6 (yes/no), trust (1-7), opened_evidence (0/1),
    attention (pass/fail), seconds."""
    probes = {p: q for p, q, _ in PROBES}
    keys = {pid: ('yes' if f(evidence()[1]) else 'no') for pid, _, f in PROBES}
    targets = {s['id']: s['targets'] for s in STIMULI}
    rows, excluded, seen = [], 0, set()
    for r in csv.DictReader(open(args.responses)):
        if not keep(r, seen):
            excluded += 1
            continue
        t = targets[r['stimulus']]
        u = [p for p in probes if p not in t]
        rows.append({'participant': r['participant'], 'condition': r['condition'], 'stimulus': r['stimulus'],
                     'acc': sum(r[p].strip().lower() == keys[p] for p in t)/len(t),
                     'untargeted': sum(r[p].strip().lower() == keys[p] for p in u)/len(u),
                     'trust': float(r['trust']), 'opened': int(r['opened_evidence'])})
    out = {'n': len(rows), 'excluded': excluded, 'by_condition': {}}
    for c in CONDITIONS:
        g = [r for r in rows if r['condition'] == c]
        if g:
            out['by_condition'][c] = {'n': len(g), 'targeted_acc': round(statistics.mean(r['acc'] for r in g), 3),
                                      'untargeted_acc': round(statistics.mean(r['untargeted'] for r in g), 3),
                                      'trust': round(statistics.mean(r['trust'] for r in g), 2),
                                      'opened_evidence': round(statistics.mean(r['opened'] for r in g), 3)}
    for a, b, name in (('M', 'C', 'H1_primary_M_lt_C'), ('M', 'N', 'H1b_M_lt_N')):
        d, p = perm_test(rows, a, b)
        out[name] = {'mean_difference': round(d, 3), 'p_one_sided': round(p, 4)}
    # trust: does M receive at least as much trust as C? (two-sided permutation on the trust means)
    tr = [dict(r, acc=r['trust']) for r in rows]
    d, p_lo = perm_test(tr, 'M', 'C')
    out['H2_trust_M_minus_C'] = {'mean_difference': round(d, 3), 'p_two_sided': round(min(1, 2*min(p_lo, 1 - p_lo)), 4)}
    try:  # secondary: probe-level GEE logit with participant clusters and stimulus fixed effects
        import pandas as pd
        import statsmodels.api as sm
        import statsmodels.formula.api as smf
        long = []
        seen = set()
        for r in csv.DictReader(open(args.responses)):
            if not keep(r, seen):
                continue
            for p in targets[r['stimulus']]:
                long.append({'participant': r['participant'], 'condition': r['condition'], 'stimulus': r['stimulus'],
                             'correct': int(r[p].strip().lower() == keys[p])})
        df = pd.DataFrame(long)
        fit = smf.gee('correct ~ C(condition, Treatment("C")) + C(stimulus)', 'participant', df,
                      family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable()).fit()
        out['secondary_gee'] = {k: {'coef': round(v, 3), 'p': round(fit.pvalues[k], 4)}
                                for k, v in fit.params.items() if 'condition' in k}
    except Exception as exc:
        out['secondary_gee'] = f'not run: {exc}'
    print(json.dumps(out, indent=2))
    if args.out:
        args.out.write_text(json.dumps(out, indent=2) + '\n')


INSTRUMENT = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Advisor Brief Study</title>
<style>
:root{--bg:#fff;--fg:#1d1d1f;--muted:#5f6368;--line:#d0d4d9;--accent:#1a5fb4}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#1b1c1e;--fg:#e8e8e8;--muted:#a0a4a8;--line:#3a3d41;--accent:#78aeed}}
:root[data-theme="dark"]{--bg:#1b1c1e;--fg:#e8e8e8;--muted:#a0a4a8;--line:#3a3d41;--accent:#78aeed}
body{background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif;max-width:760px;margin:0 auto;padding:16px}
section{display:none}section.on{display:block}button{font:inherit;padding:.5em 1em;margin:.5em 0;cursor:pointer}
table{border-collapse:collapse;font-size:14px;width:100%}td,th{border:1px solid var(--line);padding:2px 6px;text-align:right}
.brief{border:1px solid var(--line);padding:12px;border-radius:6px}.muted{color:var(--muted)}label{display:block;margin:.25em 0}
.q{margin:1em 0;padding-bottom:.5em;border-bottom:1px solid var(--line)}#ev{overflow-x:auto}pre{white-space:pre-wrap;word-break:break-all}
</style></head><body>
<section id="s0" class="on"><h1>Advisor brief study</h1>
<p>Enter the participant code you were given. The researcher assigns the code; do not enter your name.</p>
<label>Participant code <input id="pid" autocomplete="off"></label>
<label>Assignment number <input id="k" type="number" min="0"></label>
<p class="muted">By continuing you confirm that you read the information sheet and agree to take part.</p>
<button onclick="start()">Continue</button></section>
<section id="s1"><h2>The task</h2>
<p>An engineer must choose one of four scheduler configurations to minimize the 95th-percentile (P95) wake-up latency of a periodic task (lower is better). An AI advisor read the measurements below and wrote a brief. Read the brief, then answer the questions. You may open the measurements at any time.</p>
<div class="brief"><p><b>Recommended configuration:</b> <span id="cfg"></span></p><p><b>Cited evidence:</b> <span id="cit"></span></p><p id="rat"></p></div>
<p><button onclick="toggleEv()">Show / hide the measurements</button></p><div id="ev" hidden></div>
<h3>Questions about the measurements</h3><div id="qs"></div>
<div class="q">How much do you trust the advisor's brief? <div id="trust"></div></div>
<div class="q">To show you are reading carefully, select "no" here. <label><input type="radio" name="att" value="yes"> yes</label><label><input type="radio" name="att" value="no"> no</label></div>
<button onclick="finish()">Submit</button></section>
<section id="s2"><h2>Thank you</h2><p>The brief you saw was written by a language model. Some of these briefs misstate the measurements even though the recommendation is correct. Correct answers: <span id="key"></span></p>
<p>Please save your response file and return it to the researcher.</p><button onclick="save()">Save response file</button><pre id="out" class="muted"></pre></section>
<script>
const D=/*DATA*/null, C=['M','C','N'];let st,cond,t0=Date.now(),opened=0,openedAt=null,row;
function start(){const k=+document.getElementById('k').value, pid=document.getElementById('pid').value.trim();
 if(!pid||isNaN(k))return alert('Enter both fields.');cond=C[k%3];st=D.stimuli[Math.floor(k/3)%D.stimuli.length];
 row={participant:pid,assignment:k,condition:cond,stimulus:st.id};
 document.getElementById('cfg').textContent=st.config;document.getElementById('cit').textContent=st.cited_ids.join(', ');
 document.getElementById('rat').innerHTML=cond==='N'?'':'<b>Rationale:</b> '+esc(st[cond]);
 const tab=D.evidence.find(e=>e.id==='training-table').values, runs={};
 D.evidence.filter(e=>e.kind==='retrieval').forEach(e=>{const b=e.id.split('-')[2];(runs[b]=runs[b]||{})[e.config]=e.p95_us});
 const cs=Object.keys(tab);let h='<p><b>training-table</b>: mean P95 (us) per configuration</p><table><tr>'+cs.map(c=>'<th>'+c+'</th>').join('')+'</tr><tr>'+cs.map(c=>'<td>'+tab[c]+'</td>').join('')+'</tr></table>';
 h+='<p><b>retrieval runs</b>: P95 (us), period 3 ms; block b holds runs retrieval-3-b-&lt;config&gt;</p><table><tr><th>block</th>'+cs.map(c=>'<th>'+c+'</th>').join('')+'</tr>'+Object.keys(runs).sort((a,b)=>a-b).map(b=>'<tr><td>'+b+'</td>'+cs.map(c=>'<td>'+runs[b][c]+'</td>').join('')+'</tr>').join('')+'</table>';
 document.getElementById('ev').innerHTML=h;
 document.getElementById('qs').innerHTML=D.probes.map(p=>'<div class="q">'+esc(p.question)+'<label><input type="radio" name="'+p.id+'" value="yes"> yes</label><label><input type="radio" name="'+p.id+'" value="no"> no</label><label><input type="radio" name="'+p.id+'" value="unsure"> not sure</label></div>').join('');
 document.getElementById('trust').innerHTML=[1,2,3,4,5,6,7].map(v=>'<label style="display:inline"><input type="radio" name="trust" value="'+v+'"> '+v+'</label> ').join('')+'<div class="muted">1 = not at all, 7 = completely</div>';
 show('s1');t0=Date.now()}
function toggleEv(){const e=document.getElementById('ev');e.hidden=!e.hidden;if(!e.hidden){opened++;if(openedAt===null)openedAt=(Date.now()-t0)/1000}}
function val(n){const x=document.querySelector('input[name="'+n+'"]:checked');return x?x.value:''}
function finish(){for(const p of D.probes)row[p.id]=val(p.id);row.trust=val('trust');
 if(D.probes.some(p=>!row[p.id])||!row.trust||!val('att'))return alert('Please answer every question.');
 row.attention=val('att')==='no'?'pass':'fail';row.opened_evidence=opened>0?1:0;row.evidence_opens=opened;
 row.first_open_seconds=openedAt===null?'':openedAt.toFixed(1);row.seconds=((Date.now()-t0)/1000).toFixed(1);
 document.getElementById('key').textContent=D.probes.map(p=>p.id+' '+p.answer).join(', ');
 document.getElementById('out').textContent=csv();show('s2')}
function csv(){const k=Object.keys(row);return k.join(',')+'\n'+k.map(x=>'"'+String(row[x]).replace(/"/g,'""')+'"').join(',')+'\n'}
function save(){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv()],{type:'text/csv'}));a.download='response-'+row.participant+'.csv';a.click()}
function show(id){document.querySelectorAll('section').forEach(s=>s.classList.toggle('on',s.id===id));scrollTo(0,0)}
function esc(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
</script></body></html>
'''


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    b = sub.add_parser('build'); b.add_argument('--out', type=Path, required=True)
    p = sub.add_parser('power'); p.add_argument('--sims', type=int, default=300)
    p.add_argument('--n', type=int, nargs='+', default=[20, 30, 40, 50])
    p.add_argument('--p-ok', type=float, default=0.8); p.add_argument('--p-m', type=float, default=0.55)
    p.add_argument('--sd', type=float, default=1.0)
    a = sub.add_parser('analyze'); a.add_argument('--responses', type=Path, required=True); a.add_argument('--out', type=Path)
    args = ap.parse_args()
    {'build': build, 'power': power, 'analyze': analyze}[args.cmd](args)


if __name__ == '__main__':
    main()
