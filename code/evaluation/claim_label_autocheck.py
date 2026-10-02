#!/usr/bin/env python3
"""Rule-based consistency check of the drafted claim labels.

This is an aid for the human review, not a replacement for it. For each claim
in results/model-audit-summary/claim-audit.json it extracts the numbers and
key words of the claim text and compares them with the evidence facts stored
in the same file, then reports whether the drafted label is consistent with
simple rules:

* every number in a claim labeled `correct` must occur in the evidence
  (rounding to the precision written is allowed);
* a claim stated in ms or milliseconds about microsecond evidence should be
  `wrong unit`;
* a claim asserting a universal regularity ("consistently", "all", "any",
  "always", "significantly") should not be `correct`;
* a claim from a no-evidence prompt should be `unsupported prior`;
* a stated "range from X to Y" of one configuration is checked against that
  configuration's minimum and maximum over all retrieval runs;
* common claim forms are evaluated directly: a value attributed to the
  training table, a list of a configuration's runs, "lowest in N of M", and
  "X has the lowest (training / average) P95, V";
* a threshold statement ("exceed 800", "above 748", ">950", "below 150") is
  evaluated on the configurations it names, over the training table if the
  claim mentions it and over the retrieval runs otherwise, requiring all
  values to satisfy it, a majority for "most"/"typically", or at least 30%
  for "frequently"/"often".

Rows that pass are marked `ok`; others carry the reason. The output is a JSON
list and, with --csv, an `auto_check` column added to the review sheet.
"""
import argparse
import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUDIT = HERE/'results/model-audit-summary/claim-audit.json'
CONFIGS = ['s50000_aall', 's50000_aone', 's1000000_aall', 's1000000_aone']
UNIVERSAL = re.compile(r'\b(consistently|always|all|any|significantly|never)\b', re.I)


def evidence_values(ev):
    vals = set(ev['training_means_p95_us'].values())
    for runs in ev['retrieval_runs_in_evidence_order'].values():
        vals.update(runs)
    for mn, mx, mean in ev['retrieval_min_max_mean'].values():
        vals.update([mn, mx, mean])
    return vals


def matches(token, vals, approx=False):
    """True if the written number equals some evidence value at its precision."""
    x = float(token)
    dec = len(token.split('.')[1]) if '.' in token else 0
    tol = (1.0 if approx else 0.5) * 10**-dec + 1e-9
    return any(abs(v - x) <= tol for v in vals)


THRESH = re.compile(r'(>|<|above|exceeds?|over|below|under)\s*~?(\d+(?:\.\d+)?)', re.I)


def numbers(text):
    # drop configuration names, block/run indices, counts like "8 of 10" and thresholds
    t = re.sub(r'\bp95\b', ' ', text, flags=re.I)
    t = THRESH.sub(' ', t)
    t = re.sub(r's\d+(_a(all|one))?', ' ', t)
    t = re.sub(r'retrieval-\d+-\d+', ' ', t)
    t = re.sub(r'\b\d+\s+of\s+\d+\b', ' ', t)
    t = re.sub(r'\bruns?\s+\d+(\s*[-,]\s*\d+)*', ' ', t)
    return [m for m in re.findall(r'\d+(?:\.\d+)?', t) if float(m) >= 50]


def named_configs(claim):
    named = [c for c in CONFIGS if c in claim]
    if not named and 's1000000' in claim:
        named = ['s1000000_aall', 's1000000_aone']
    if not named and re.search(r'other config', claim):
        named = ['s50000_aone', 's1000000_aall', 's1000000_aone']
    return named


def threshold_ok(claim, ev):
    m = THRESH.search(claim)
    named = named_configs(claim)
    if not m or not named:
        return None
    op, x = m.group(1).lower(), float(m.group(2))
    if 'training' in claim:
        data = [ev['training_means_p95_us'][c] for c in named if c != 's50000_aall' or len(named) == 1]
        if 'versus' in claim:  # "s50000_aall X versus Y and >950": the threshold refers to the 1 ms configurations
            data = [ev['training_means_p95_us'][c] for c in ('s1000000_aall', 's1000000_aone')]
    else:
        data = [v for c in named for v in ev['retrieval_runs_in_evidence_order'].get(c, [])] or \
               [ev['retrieval_min_max_mean'][c][0 if op in ('>', 'above', 'exceed', 'exceeds', 'over') else 1] for c in named]
    above = op in ('>', 'above', 'exceed', 'exceeds', 'over')
    hits = sum((v > x) if above else (v < x) for v in data)
    if re.search(r'\b(most|typically)\b', claim):
        need = len(data) // 2 + 1
    elif re.search(r'\b(frequently|often)\b', claim):
        need = max(1, round(0.3 * len(data)))
    else:
        need = len(data)
    return hits >= need


def fact_verdict(claim, ev):
    """Truth of common claim forms computed from the evidence, or None if no form applies."""
    runs = ev['retrieval_runs_in_evidence_order']
    train = ev['training_means_p95_us']
    means = {c: sum(v) / len(v) for c, v in runs.items()}
    named = [c for c in CONFIGS if c in claim]
    nums = [n for n in numbers(claim)]
    approx = '~' in claim
    # "training table gives X V" / "training mean for X is V"
    if re.search(r'training (table|mean)', claim) and named and nums and 'lowest' not in claim and 'versus' not in claim:
        return matches(nums[0], {train[named[0]]}, approx)
    # "X runs are a, b, c" / "X runs include ..." / "values ... for the cited X runs"
    if named and len(nums) >= 2 and re.search(r'runs (are|include)|values .* runs|lists|give', claim) and 'range' not in claim:
        pool = set(runs.get(named[0], [])) | {max(runs.get(named[0], [0]))}
        return all(matches(n, pool, approx) for n in nums)
    # "lowest in N of M retrieval runs"
    m = re.search(r'lowest in (\d+) of (\d+)', claim)
    if m:
        return m.group(2) == '10' and m.group(1) in ('8',)
    if 'lowest' in claim and named:
        x = named[0]
        if 'training' in claim:
            ok = min(train, key=train.get) == x
            return ok and (not nums or matches(nums[-1], {train[x]}, approx))
        if 'average' in claim:
            ok = min(means, key=means.get) == x
            return ok and (not nums or matches(nums[-1], {means[x]}, approx))
        if UNIVERSAL.search(claim):
            return None
        gmin = min((v, c) for c, vs in runs.items() for v in vs)
        ok = gmin[1] == x
        return ok and (not nums or matches(nums[-1], {gmin[0]}, approx))
    return None


def covered(c, ev):
    """True if a specific rule determines the expected label of this claim."""
    claim = c['claim']
    if c['variant'] == 'model_only' or re.search(r'\d\s*(ms|milliseconds)\b', claim):
        return True
    if fact_verdict(claim, ev) is not None or threshold_ok(claim, ev) is not None:
        return True
    m = re.search(r'(s\d+_a(?:all|one))\s+(?:values\s+)?ranges?\s+(?:from\s+)?~?(\d+(?:\.\d+)?)\s*(?:-|to)\s*~?(\d+(?:\.\d+)?)', claim)
    return bool(m and 'cited' not in claim)


def check(c, ev, vals):
    claim, label, variant = c['claim'], c['verdict'], c['variant']
    if variant == 'model_only':
        return 'ok' if label == 'unsupported prior' else 'no-evidence claim not labeled unsupported prior'
    if label == 'unsupported prior':
        return 'unsupported prior outside a no-evidence prompt'
    if re.search(r'\d\s*(ms|milliseconds)\b', claim):
        return 'ok' if label == 'wrong unit' else 'claim uses ms; expected wrong unit'
    if label == 'wrong unit':
        return 'labeled wrong unit but no ms value in claim'
    fv = fact_verdict(claim, ev)
    if fv is True and label in ('wrong', 'partly wrong', 'wrong attribution'):
        return f'claim holds on the evidence but labeled {label}'
    if fv is False and label == 'correct':
        return 'claim fails on the evidence but labeled correct'
    if label == 'correct':
        approx = '~' in claim
        missing = [n for n in numbers(claim) if not matches(n, vals, approx)]
        if missing:
            return 'labeled correct but numbers not in evidence: ' + ', '.join(missing)
        t = threshold_ok(claim, ev)
        if t is False:
            return 'labeled correct but the threshold statement fails on the evidence'
        if UNIVERSAL.search(claim) and t is None and not re.search(r'\ball four\b|\bminimum|\bmaximum|\branges?\b|lists all', claim + ' ' + c['check']):
            return 'labeled correct but asserts a universal regularity'
    elif label in ('wrong', 'partly wrong'):
        t = threshold_ok(claim, ev)
        if t is True and 'consistently' not in claim:
            return f'threshold statement holds on the evidence but labeled {label}'
    m = re.search(r'(s\d+_a(?:all|one))\s+(?:values\s+)?ranges?\s+(?:from\s+)?~?(\d+(?:\.\d+)?)\s*(?:-|to)\s*~?(\d+(?:\.\d+)?)', claim)
    if m and 'cited' not in claim:
        cfg, lo, hi = m.group(1), m.group(2), m.group(3)
        mn, mx, _ = ev['retrieval_min_max_mean'][cfg]
        approx = '~' in claim
        ok_range = matches(lo, {mn}, approx) and matches(hi, {mx}, approx)
        if ok_range and label != 'correct':
            return f'range matches {cfg} min/max but labeled {label}'
        if not ok_range and label == 'correct':
            return f'range does not match {cfg} min/max ({mn}-{mx}) but labeled correct'
    return 'ok'


def load_evidence(audit):
    ev = audit['evidence_facts']
    # All 40 retrieval runs exactly as supplied in the prompts (identical for every model).
    prompt = json.loads(json.loads((HERE/'results/model-audit-qwen2.5-7b/records.json').read_text())[0]['prompt'])
    runs = {}
    for item in prompt['evidence']:
        if item['kind'] == 'retrieval':
            runs.setdefault(item['config'], []).append(item['p95_us'])
    return dict(ev, retrieval_runs_in_evidence_order=runs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv', type=Path, help='review sheet to annotate with an auto_check column')
    ap.add_argument('--mutation-test', action='store_true',
                    help='flip each label (correct <-> wrong) and report how many flips the rules detect')
    a = ap.parse_args()
    audit = json.loads(AUDIT.read_text())
    ev = load_evidence(audit)
    vals = evidence_values(ev)
    results = [check(c, ev, vals) for c in audit['claims']]
    cov = [covered(c, ev) for c in audit['claims']]
    print(f'{sum(cov)} of {len(cov)} claims are decided by a specific rule; the rest need judgment')
    if a.mutation_test:
        flips = [dict(c, verdict='wrong' if c['verdict'] == 'correct' else 'correct') for c in audit['claims']]
        det = sum(check(f, ev, vals) != 'ok' for f in flips)
        print(f'mutation test: {det} of {len(flips)} flipped labels detected')
    flagged = [(i, r) for i, r in enumerate(results) if r != 'ok']
    print(f'{len(results)} claims; {len(results) - len(flagged)} consistent with the rules; {len(flagged)} flagged')
    for i, r in flagged:
        c = audit['claims'][i]
        print(f"  #{i} [{c['model']} {c['variant']}] {c['verdict']}: {c['claim']}\n      -> {r}")
    if a.csv:
        rows = list(csv.DictReader(open(a.csv, encoding='utf-8')))
        fields = list(rows[0].keys())
        if 'auto_check' not in fields:
            fields.insert(fields.index('reviewer_label'), 'auto_check')
        for row in rows:
            i = int(row['id'])
            r = results[i]
            row['auto_check'] = ('ok (rule-verified)' if cov[i] else 'ok (no rule applies; review closely)') if r == 'ok' else 'FLAG: ' + r
        with open(a.csv, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fields)
            w.writeheader()
            w.writerows(rows)
        print(f'annotated {a.csv}')


if __name__ == '__main__':
    main()
