#!/usr/bin/env python3
"""Export the drafted claim labels for human review, and score the review.

    python3 claim_review_agreement.py export --out ../../paper/claim-label-review.csv
    python3 claim_review_agreement.py score  --review ../../paper/claim-label-review.csv
    python3 claim_review_agreement.py score  --review ... --apply
    python3 claim_review_agreement.py export-blind --out second-annotator.csv
    python3 claim_review_agreement.py kappa --second second-annotator.csv
    python3 claim_review_agreement.py kappa --second third.csv --key third_annotator
    python3 claim_review_agreement.py panel second-annotator.csv third.csv

`export-blind` writes the same claims for an independent second annotator
without the drafted labels or checks, with the explanation sentence that
states each claim. `kappa` compares the second annotator's labels with the
verified labels in claim-audit.json (Cohen's kappa over all seven labels and
over the binary misstated / not-misstated distinction) and writes the result
into claim-audit.json under "second_annotator" (or --key), keeping fields
written by hand. `panel` reports Fleiss' kappa over the verified labels and
all blind annotators, and how often their majority label equals the verified
label.

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
    # Optional 'seed' and 'source_hint' fields in a claim pin its explanation
    # and sentence where the number/word scoring would pick another one.
    import re
    recs = [r for r in json.loads((HERE/f"results/model-audit-{DIRS[c['model']]}/records.json").read_text())
            if r.get('variant') == c['variant'] and r.get('status') == 'valid'
            and ('seed' not in c or r.get('seed') == c['seed'])]
    nums = re.findall(r'\d+(?:\.\d+)?', c['claim'])
    words = re.findall(r'[a-z]{5,}', c['claim'].lower())

    def sc(t):
        return 3 * sum(n in t for n in nums) + sum(w in t.lower() for w in words)
    expl = max((r['answer']['explanation'] for r in recs), key=sc)
    sents = [x for x in re.split(r'(?<=[.;])\s+', expl) if x.strip()]
    if 'source_hint' in c:  # claims whose sentence the scoring heuristic misses
        sents = [x for x in sents if c['source_hint'] in x]
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


def read_annotator(path, n):
    rows = list(csv.DictReader(open(path, encoding='utf-8-sig')))
    if len(rows) != n or any(not r['second_label'].strip() for r in rows):
        raise SystemExit(f'{path}: the annotator must label every row')
    labels = [None] * n
    for r in rows:
        lab = r['second_label'].strip().lower()
        if lab not in LABELS:
            raise SystemExit(f"{path} row {r['id']}: unknown label {lab!r}")
        labels[int(r['id'])] = lab
    return labels


def kappa(args):
    """Compare one blind annotator with the verified labels.

    The result is merged into claim-audit.json under --key, so fields written
    by hand (annotator description, resolution) are kept.
    """
    audit = json.loads(AUDIT.read_text())
    first = [c['verdict'] for c in audit['claims']]
    second = read_annotator(args.second, len(first))
    po, k = cohen_kappa(first, second)
    pb, kb = cohen_kappa([x in MISSTATED for x in first], [x in MISSTATED for x in second])
    print(f'seven labels: agreement {po:.3f}, kappa {k:.3f}; misstated vs not: agreement {pb:.3f}, kappa {kb:.3f}')
    rec = audit.get(args.key, {})
    notes = {d['id']: d['note'] for d in rec.get('disagreements', []) if d.get('note')}
    disagreements = []
    for i, (v, lab) in enumerate(zip(first, second)):
        if v != lab:
            disagreements.append({'id': i, 'verified': v, 'annotator': lab, **({'note': notes[i]} if i in notes else {})})
    rec.update({'claims': len(first), 'agreement_7': round(po, 4), 'kappa_7': round(k, 4),
                'agreement_binary': round(pb, 4), 'kappa_binary': round(kb, 4),
                'procedure': 'independent annotator labeled blind (without drafted labels or checks)',
                'disagreements': disagreements,
                'misstated_by_annotator': sum(x in MISSTATED for x in second)})
    rec.pop('misstated_by_second_annotator', None)
    audit[args.key] = rec
    AUDIT.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n')


def fleiss_kappa(table):
    """Fleiss' kappa for a list of per-item label lists (same rater count)."""
    n_items, n = len(table), len(table[0])
    totals = collections.Counter()
    p_items = []
    for labels in table:
        c = collections.Counter(labels)
        totals.update(c)
        p_items.append((sum(v * v for v in c.values()) - n) / (n * (n - 1)))
    p_bar = sum(p_items) / n_items
    p_e = sum((v / (n_items * n)) ** 2 for v in totals.values())
    return (p_bar - p_e) / (1 - p_e)


def panel(args):
    """Agreement of the verified labels and all blind annotators together.

    Reports Fleiss' kappa (seven labels and misstated vs not), pairwise Cohen's
    kappa between annotators, and how often the majority label equals the
    verified label; writes the result under "annotator_panel".
    """
    audit = json.loads(AUDIT.read_text())
    verified = [c['verdict'] for c in audit['claims']]
    annot = [read_annotator(p, len(verified)) for p in args.annotators]
    raters = [verified] + annot
    items = list(zip(*raters))
    f7 = fleiss_kappa(items)
    fb = fleiss_kappa([[x in MISSTATED for x in it] for it in items])
    majority, no_majority = [], 0
    for it in items:
        lab, cnt = collections.Counter(it).most_common(1)[0]
        no_majority += cnt * 2 <= len(it)
        majority.append(lab)
    same = sum(m == v for m, v in zip(majority, verified))
    pairs = {}
    for i in range(len(annot)):
        for j in range(i + 1, len(annot)):
            _, k = cohen_kappa(annot[i], annot[j])
            _, kb = cohen_kappa([x in MISSTATED for x in annot[i]], [x in MISSTATED for x in annot[j]])
            pairs[f'{i + 2}-{j + 2}'] = {'kappa_7': round(k, 4), 'kappa_binary': round(kb, 4)}
    print(f'Fleiss kappa: seven labels {f7:.3f}, misstated vs not {fb:.3f}; '
          f'majority = verified label for {same} of {len(verified)} claims ({no_majority} without majority)')
    for key, v in pairs.items():
        print(f'annotators {key}: kappa {v["kappa_7"]:.3f} (seven labels), {v["kappa_binary"]:.3f} (binary)')
    audit['annotator_panel'] = {
        'raters': ['author-verified labels'] + [f'blind annotator {i + 2}' for i in range(len(annot))],
        'fleiss_kappa_7': round(f7, 4), 'fleiss_kappa_binary': round(fb, 4),
        'majority_equals_verified': same, 'items_without_majority': no_majority,
        'pairwise_annotators': pairs}
    AUDIT.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n')


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    e = sub.add_parser('export'); e.add_argument('--out', required=True, type=Path)
    s = sub.add_parser('score'); s.add_argument('--review', required=True, type=Path)
    s.add_argument('--apply', action='store_true')
    b = sub.add_parser('export-blind'); b.add_argument('--out', required=True, type=Path)
    k = sub.add_parser('kappa'); k.add_argument('--second', required=True, type=Path)
    k.add_argument('--key', default='second_annotator', help='record name in claim-audit.json')
    p = sub.add_parser('panel'); p.add_argument('annotators', nargs='+', type=Path)
    a = ap.parse_args()
    {'export': export, 'score': score, 'export-blind': export_blind, 'kappa': kappa, 'panel': panel}[a.cmd](a)


if __name__ == '__main__':
    main()
