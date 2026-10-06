#!/usr/bin/env python3
"""Export the drafted claim labels for human review, and score the review.

    python3 claim_review_agreement.py export --out ../../paper/claim-label-review.csv
    python3 claim_review_agreement.py score  --review ../../paper/claim-label-review.csv
    python3 claim_review_agreement.py score  --review ... --apply
    python3 claim_review_agreement.py export-blind --out second-annotator.csv
    python3 claim_review_agreement.py kappa --second second-annotator.csv

`export-blind` writes the same claims for an independent second annotator
without the drafted labels or checks, with the explanation sentence that
states each claim. `kappa` compares the second annotator's labels with the
verified labels in claim-audit.json (Cohen's kappa over all seven labels and
over the binary misstated / not-misstated distinction) and writes the result
into claim-audit.json under "second_annotator".

`export` writes one row per claim in results/model-audit-summary/claim-audit.json
with the drafted label and its check, plus empty columns for the reviewer.
The reviewer leaves `reviewer_label` empty to accept the drafted label, or
enters one of LABELS to change it, and may add a note.

`score` reports raw agreement and Cohen's kappa between the drafted and the
reviewed labels, per label and overall. With --apply it writes the reviewed
labels back into claim-audit.json, marks the audit as human-verified and
records the agreement, so claim_taxonomy.py then tabulates verified labels.
"""
import argparse
import collections
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUDIT = HERE/'results/model-audit-summary/claim-audit.json'
LABELS = ['correct', 'overstated', 'wrong', 'partly wrong', 'wrong unit',
          'wrong attribution', 'unsupported prior']
FIELDS = ['id', 'model', 'variant', 'claim', 'drafted_label', 'check',
          'reviewer_label', 'reviewer_note']


def cohen_kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = collections.Counter(a), collections.Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n**2
    return po, (po - pe) / (1 - pe) if pe < 1 else 1.0


def export(args):
    audit = json.loads(AUDIT.read_text())
    with open(args.out, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        for i, c in enumerate(audit['claims']):
            w.writerow({'id': i, 'model': c['model'], 'variant': c['variant'], 'claim': c['claim'],
                        'drafted_label': c['verdict'], 'check': c['check'],
                        'reviewer_label': '', 'reviewer_note': ''})
    print(f"wrote {len(audit['claims'])} rows to {args.out}")


def score(args):
    audit = json.loads(AUDIT.read_text())
    claims = audit['claims']
    rows = list(csv.DictReader(open(args.review, encoding='utf-8')))
    if len(rows) != len(claims):
        raise SystemExit(f'review has {len(rows)} rows, audit has {len(claims)} claims')
    drafted, reviewed = [], []
    for r in rows:
        c = claims[int(r['id'])]
        if c['claim'] != r['claim'] or c['verdict'] != r['drafted_label']:
            raise SystemExit(f"row {r['id']} does not match the audit; re-export the sheet")
        label = (r['reviewer_label'] or '').strip().lower() or c['verdict']
        if label not in LABELS:
            raise SystemExit(f"row {r['id']}: unknown label {label!r}; use one of {LABELS}")
        drafted.append(c['verdict'])
        reviewed.append(label)
    po, kappa = cohen_kappa(drafted, reviewed)
    changed = [(i, d, r) for i, (d, r) in enumerate(zip(drafted, reviewed)) if d != r]
    print(f'claims: {len(rows)}; changed: {len(changed)}; agreement {po:.3f}; Cohen kappa {kappa:.3f}')
    for i, d, r in changed:
        print(f'  #{i}: {d} -> {r}')
    if args.apply:
        for c, label, row in zip(claims, reviewed, rows):
            c['drafted_verdict'] = c.get('drafted_verdict', c['verdict'])
            c['verdict'] = label
            if row.get('reviewer_note'):
                c['reviewer_note'] = row['reviewer_note']
        audit['verification'] = {'human_verified': True,
                                 'procedure': 'One author reviewed every AI-drafted label against the prompt evidence.',
                                 'changed_labels': len(changed),
                                 'agreement_with_draft': round(po, 4),
                                 'cohen_kappa_with_draft': round(kappa, 4)}
        AUDIT.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n')
        print(f'applied to {AUDIT}')


MISSTATED = {'wrong', 'wrong attribution', 'wrong unit', 'overstated'}
DIRS = {'Qwen2.5-7B': 'qwen2.5-7b', 'Llama-3.1-8B': 'llama3.1-8b', 'Qwen2.5-14B': 'qwen2.5-14b', 'Phi-4': 'phi-4',
        'Llama-3.3-70B': 'api-llama3.3-70b', 'Qwen3-235B': 'api-qwen3-235b', 'DeepSeek-V3.2': 'api-deepseek-v3.2',
        'Nemotron-3-Ultra-550B': 'api-nemotron3-ultra-550b', 'Gemini-3.8-Flash': 'api-gemini-3.8-flash',
        'Gemini-3.1-Pro': 'api-gemini-3.1-pro'}


def source_sentence(c):
    import re
    recs = [r for r in json.loads((HERE/f"results/model-audit-{DIRS[c['model']]}/records.json").read_text())
            if r.get('variant') == c['variant'] and r.get('status') == 'valid']
    nums = re.findall(r'\d+(?:\.\d+)?', c['claim'])
    words = re.findall(r'[a-z]{5,}', c['claim'].lower())

    def sc(t):
        return 3 * sum(n in t for n in nums) + sum(w in t.lower() for w in words)
    expl = max((r['answer']['explanation'] for r in recs), key=sc)
    sents = [x for x in re.split(r'(?<=[.;])\s+', expl) if x.strip()]
    return max(sents, key=sc), bool(json.loads(recs[0]['prompt'])['evidence'])


def export_blind(args):
    audit = json.loads(AUDIT.read_text())
    with open(args.out, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, ['id', 'model', 'variant', 'evidence_supplied', 'source_sentence', 'claim',
                               'second_label', 'second_note'])
        w.writeheader()
        for i, c in enumerate(audit['claims']):
            sent, has_ev = source_sentence(c)
            w.writerow({'id': i, 'model': c['model'], 'variant': c['variant'],
                        'evidence_supplied': 'yes' if has_ev else 'no', 'source_sentence': sent,
                        'claim': c['claim'], 'second_label': '', 'second_note': ''})
    print(f"wrote {len(audit['claims'])} blind rows to {args.out}")


def kappa(args):
    audit = json.loads(AUDIT.read_text())
    rows = list(csv.DictReader(open(args.second, encoding='utf-8')))
    if len(rows) != len(audit['claims']) or any(not r['second_label'].strip() for r in rows):
        raise SystemExit('the second annotator must label every row')
    first, second = [], []
    for r in rows:
        lab = r['second_label'].strip().lower()
        if lab not in LABELS:
            raise SystemExit(f"row {r['id']}: unknown label {lab!r}")
        first.append(audit['claims'][int(r['id'])]['verdict'])
        second.append(lab)
    po, k = cohen_kappa(first, second)
    pb, kb = cohen_kappa([x in MISSTATED for x in first], [x in MISSTATED for x in second])
    print(f'seven labels: agreement {po:.3f}, kappa {k:.3f}; misstated vs not: agreement {pb:.3f}, kappa {kb:.3f}')
    audit['second_annotator'] = {'claims': len(rows), 'agreement_7': round(po, 4), 'kappa_7': round(k, 4),
                                 'agreement_binary': round(pb, 4), 'kappa_binary': round(kb, 4),
                                 'procedure': 'independent annotator labeled blind (without drafted labels or checks)'}
    AUDIT.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n')


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    e = sub.add_parser('export'); e.add_argument('--out', required=True, type=Path)
    s = sub.add_parser('score'); s.add_argument('--review', required=True, type=Path)
    s.add_argument('--apply', action='store_true')
    b = sub.add_parser('export-blind'); b.add_argument('--out', required=True, type=Path)
    k = sub.add_parser('kappa'); k.add_argument('--second', required=True, type=Path)
    a = ap.parse_args()
    {'export': export, 'score': score, 'export-blind': export_blind, 'kappa': kappa}[a.cmd](a)


if __name__ == '__main__':
    main()
