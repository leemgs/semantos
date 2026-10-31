#!/usr/bin/env python3
"""Third blind annotation round: claim extraction and the SQLite readings (not yet run).

Two gaps remain after the main annotation study.
(A) Annotators labeled claims that had already been extracted, so the
    extraction step itself was never checked independently.
(B) The SQLite readings of §5.5 / Appendix K were drafted with an AI assistant
    and verified by one author, with no blind annotator.

This script writes blind sheets for one new annotator and scores the returned
sheets against the paper's labels. It never writes labels itself.

    python3 blind_round3.py export --out ../../paper/annotation-round3
    python3 blind_round3.py score --dir ../../paper/annotation-round3 [--json results/model-audit-summary/blind-round3.json]

Task A (extraction): the 27 distinct full-context explanations of the main
audit. The annotator lists every quantitative or comparative claim about the
evidence, one row per claim, copying the exact text span. Scoring matches each
audited claim to an annotator span in the same explanation, using its source
sentence (claim_review_agreement.source_sentence) and a shared number or key
word. It reports recall (audited claims the annotator also extracted),
precision (annotator spans matching an audited claim) and the unmatched items
for adjudication. Matching is heuristic, so the unmatched list is the input to
a manual adjudication, not a final verdict.

Task B (SQLite readings): the 27 full-evidence SQLite explanations. The
annotator marks whether each contains a misstatement of the evidence and
whether it misreports the training table. Scoring gives Cohen's kappa
against the author-verified readings (results/domain-sqlite/explanations-read.csv).
"""
import argparse
import csv
import json
import re
from pathlib import Path

import claim_review_agreement as cra

HERE = Path(__file__).resolve().parent
RES = HERE/'results'
AUDIT = RES/'model-audit-summary/claim-audit.json'
SQLITE = RES/'domain-sqlite'


def explanations():
    """Distinct full-context explanations of the main audit, in model order."""
    out = []
    for name, d in cra.DIRS.items():
        seen = set()
        for r in json.loads((RES/f'model-audit-{d}/records.json').read_text()):
            if r['variant'] == 'full' and r.get('status') == 'valid' and r['answer']['explanation'] not in seen:
                seen.add(r['answer']['explanation'])
                out.append({'model': name, 'seed': r['seed'], 'text': r['answer']['explanation']})
    for i, e in enumerate(out, 1):
        e['id'] = f'E{i:02d}'
    return out


def audited_claims(expls):
    """Full-context audited claims, each mapped to its explanation id and source sentence."""
    audit = json.loads(AUDIT.read_text())['claims']
    rows = []
    for k, c in enumerate(audit):
        if c['variant'] != 'full':
            continue
        sent, _ = cra.source_sentence(c)
        # hosted models repeat sentences across seeds, so a claim may sit in several explanations
        nums = re.findall(r'\d+(?:\.\d+)?', c['claim'])
        words = re.findall(r'[a-z]{6,}', c['claim'].lower())

        def holds(t):  # the explanation states the same numbers (or, without numbers, the same key words)
            return all(n in t for n in nums) if nums else sum(w in t.lower() for w in words) >= max(1, len(words) - 1)
        cands = [e['id'] for e in expls if e['model'] == c['model'] and (sent in e['text'] or holds(e['text']))]
        rows.append({'claim_index': k, 'expl': cands, 'sentence': sent, 'claim': c['claim'], 'verdict': c['verdict']})
    return rows


def keys(t):
    return set(re.findall(r'\d+(?:\.\d+)?', t)) | {w for w in re.findall(r'[a-z]{6,}', t.lower())}


def export(args):
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    expls = explanations()
    with (out/'taskA-explanations.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, ['expl_id', 'explanation'])
        w.writeheader()
        w.writerows({'expl_id': e['id'], 'explanation': e['text']} for e in expls)
    with (out/'taskA-claims-template.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, ['expl_id', 'span', 'note'])
        w.writeheader()
        w.writerow({'expl_id': 'E01', 'span': '(copy the exact words of one claim here; one row per claim)', 'note': ''})
    rows = list(csv.DictReader((SQLITE/'explanations-for-review.csv').open(encoding='utf-8')))
    with (out/'taskB-sqlite-blind.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, ['id', 'config', 'explanation', 'contains_misstatement', 'misreports_training_table', 'note'])
        w.writeheader()
        for i, r in enumerate(rows, 1):  # no model names, flags or readings
            w.writerow({'id': f'S{i:02d}', 'config': r['config'], 'explanation': r['explanation'],
                        'contains_misstatement': '', 'misreports_training_table': '', 'note': ''})
    import domain_sqlite
    _, items, _ = domain_sqlite.load(SQLITE)  # the evidence the models saw (no test runs)
    with (out/'taskB-evidence.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, ['item', 'config', 'block', 'p95_us'])
        w.writeheader()
        for c, v in items[0]['values'].items():
            w.writerow({'item': 'training-table (mean)', 'config': c, 'block': '', 'p95_us': v})
        for i in items[1:]:
            w.writerow({'item': i['id'], 'config': i['config'], 'block': i['block'], 'p95_us': i['p95_us']})
    key = [{'id': f'S{i:02d}', 'model': r['model'], 'seed': r['seed']} for i, r in enumerate(rows, 1)]
    (out/'taskB-key.json').write_text(json.dumps(key, indent=2) + '\n')  # keep away from the annotator
    print(f'wrote {len(expls)} Task A explanations and {len(rows)} Task B rows to {out}')


def score(args):
    d = args.dir
    out = {}
    expls = explanations()
    ours = audited_claims(expls)
    spans = [r for r in csv.DictReader((d/'taskA-claims.csv').open(encoding='utf-8'))
             if r['span'].strip() and not r['span'].startswith('(copy')]
    used, matched = set(), []
    for c in ours:  # greedy one-to-one match within the same explanation
        best = None
        for j, s in enumerate(spans):
            if j in used or s['expl_id'] not in c['expl']:
                continue
            overlap = len(keys(s['span']) & keys(c['claim']))
            if overlap and (best is None or overlap > best[1]):
                best = (j, overlap)
        if best:
            used.add(best[0])
            matched.append(c['claim_index'])
    missed = [c for c in ours if c['claim_index'] not in matched]
    extra = [s for j, s in enumerate(spans) if j not in used]
    mis = cra.MISSTATED
    out['taskA'] = {'explanations': len(expls), 'audited_claims': len(ours), 'annotator_spans': len(spans),
                    'recall': round(len(matched)/len(ours), 3), 'precision': round(len(used)/len(spans), 3) if spans else None,
                    'audited_misstated': sum(c['verdict'] in mis for c in ours),
                    'misstated_found_by_annotator': sum(c['verdict'] in mis for c in ours if c['claim_index'] in matched),
                    'for_adjudication': {'audited_not_matched': [{'expl': ' or '.join(c['expl']), 'claim': c['claim']} for c in missed],
                                         'annotator_not_matched': [{'expl': s['expl_id'], 'span': s['span']} for s in extra]}}
    key = {k['id']: (k['model'], int(k['seed'])) for k in json.loads((d/'taskB-key.json').read_text())}
    read = {(r['model'], int(r['seed'])): r for r in csv.DictReader((SQLITE/'explanations-read.csv').open(encoding='utf-8'))}
    a_mis, b_mis, a_tab, b_tab = [], [], [], []
    yes = lambda v: v.strip().lower() in ('yes', 'y', '1', 'true')
    for r in csv.DictReader((d/'taskB-sqlite.csv').open(encoding='utf-8')):
        ref = read[key[r['id']]]
        a_mis.append(yes(r['contains_misstatement']))
        b_mis.append(ref['reading_issue'] != 'none found')
        a_tab.append(yes(r['misreports_training_table']))
        b_tab.append('table' in ref['reading_issue'])
    agree = lambda a, b: round(sum(x == y for x, y in zip(a, b))/len(a), 3)
    out['taskB'] = {'n': len(a_mis), 'misstatement': {'annotator_yes': sum(a_mis), 'author_yes': sum(b_mis),
                                                     'agreement': agree(a_mis, b_mis), 'kappa': round(cra.cohen_kappa(a_mis, b_mis)[1], 3)},
                    'training_table': {'annotator_yes': sum(a_tab), 'author_yes': sum(b_tab),
                                       'agreement': agree(a_tab, b_tab), 'kappa': round(cra.cohen_kappa(a_tab, b_tab)[1], 3)}}
    print(json.dumps({k: (v if k != 'taskA' else {x: y for x, y in v.items() if x != 'for_adjudication'}) for k, v in out.items()}, indent=2))
    if args.json:
        args.json.write_text(json.dumps(out, indent=2) + '\n')


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    e = sub.add_parser('export'); e.add_argument('--out', type=Path, required=True)
    s = sub.add_parser('score'); s.add_argument('--dir', type=Path, required=True); s.add_argument('--json', type=Path)
    a = ap.parse_args()
    {'export': export, 'score': score}[a.cmd](a)


if __name__ == '__main__':
    main()
