#!/usr/bin/env python3
"""Export the drafted claim labels for human review, and score the review.

    python3 claim_review_agreement.py export --out ../../paper/claim-label-review.csv
    python3 claim_review_agreement.py score  --review ../../paper/claim-label-review.csv
    python3 claim_review_agreement.py score  --review ... --apply

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


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    e = sub.add_parser('export'); e.add_argument('--out', required=True, type=Path)
    s = sub.add_parser('score'); s.add_argument('--review', required=True, type=Path)
    s.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    export(a) if a.cmd == 'export' else score(a)


if __name__ == '__main__':
    main()
