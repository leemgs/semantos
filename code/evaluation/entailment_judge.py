#!/usr/bin/env python3
"""Would an entailment-based attribution judge catch the misstated claims?

For every audited claim that rests on supplied evidence (the four
no-evidence "unsupported prior" claims are excluded), this script takes the
explanation sentence that states the claim (hypothesis) and the evidence items
the model cited for that answer (premise), as in citation-support evaluation
(ALCE/AIS style), and asks off-the-shelf judges whether the premise supports
the hypothesis:

* three NLI cross-encoders (entailment = supported), and
* Flan-T5-large asked "Is the claim fully supported by the evidence?"
  (yes = supported).

A second condition uses the extracted claim text instead of the sentence.
The script reports, per judge, how many misstated claims (wrong, wrong
attribution, wrong unit, overstated) are accepted as supported and how many
correct claims are accepted, using the author-verified labels in
claim-audit.json. Model revisions are pinned; runs on CPU in a few minutes.

    python3 entailment_judge.py --out results/model-audit-summary/entailment-judge.json
    python3 entailment_judge.py --out results/model-audit-summary/entailment-judge.json \
        --tex ../../paper/entailment-judges.tex   # table only, from the saved results
"""
import argparse
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE/'results'
DIRS = {'Qwen2.5-7B': 'qwen2.5-7b', 'Llama-3.1-8B': 'llama3.1-8b', 'Qwen2.5-14B': 'qwen2.5-14b', 'Phi-4': 'phi-4',
        'Llama-3.3-70B': 'api-llama3.3-70b', 'Qwen3-235B': 'api-qwen3-235b', 'DeepSeek-V3.2': 'api-deepseek-v3.2',
        'Nemotron-3-Ultra-550B': 'api-nemotron3-ultra-550b', 'Gemini-3.8-Flash': 'api-gemini-3.8-flash',
        'Gemini-3.1-Pro': 'api-gemini-3.1-pro'}
JUDGES = [
    ('DeBERTa-v3-large (MNLI/FEVER/ANLI/LingNLI/WANLI)', 'MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli',
     'b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7', 'nli'),
    ('DeBERTa-v3-large (SNLI/MNLI cross-encoder)', 'cross-encoder/nli-deberta-v3-large',
     'bab4bc7178836f731dcfd18c06ca9def0a137712', 'nli'),
    ('RoBERTa-large-MNLI', 'FacebookAI/roberta-large-mnli', '2a8f12d27941090092df78e4ba6f0928eb5eac98', 'nli'),
    ('Flan-T5-large (yes/no)', 'google/flan-t5-large', '0613663d0d48ea86ba8cb3d7a44f0f65dc596a2a', 't5'),
]
MISSTATED = {'wrong', 'wrong attribution', 'wrong unit', 'overstated'}


def verbalize(item):
    if item['kind'] == 'table':
        vals = '; '.join(f'{k} {v} microseconds' for k, v in item['values'].items())
        return f'Training table of mean P95 wake-up latency: {vals}.'
    if item['kind'] == 'graph':
        return f"Interaction item: training contrast {item['contrast_us']:.1f} microseconds; no graph edges."
    return (f"Retrieval run {item['id']}: configuration {item['config']}, period {item['period_ns'] // 1000000} ms, "
            f"P95 wake-up latency {item['p95_us']} microseconds.")


def score(text, claim):
    nums = re.findall(r'\d+(?:\.\d+)?', claim)
    words = re.findall(r'[a-z]{5,}', claim.lower())
    return 3 * sum(n in text for n in nums) + sum(w in text.lower() for w in words)


def build_items():
    audit = json.loads((RES/'model-audit-summary/claim-audit.json').read_text())
    items = []
    for i, c in enumerate(audit['claims']):
        if c['variant'] == 'model_only':
            continue
        recs = [r for r in json.loads((RES/f"model-audit-{DIRS[c['model']]}/records.json").read_text())
                if r.get('variant') == c['variant'] and r.get('status') == 'valid']
        rec = max(recs, key=lambda r: score(r['answer']['explanation'], c['claim']))
        evidence = {e['id']: e for e in json.loads(rec['prompt'])['evidence']}
        cited = [evidence[x] for x in rec['answer']['cited_ids'] if x in evidence]
        sents = [s for s in re.split(r'(?<=[.;])\s+', rec['answer']['explanation']) if s.strip()]
        sentence = max(sents, key=lambda s: score(s, c['claim']))
        items.append({'id': i, 'model': c['model'], 'variant': c['variant'], 'seed': rec['seed'],
                      'label': c['verdict'], 'claim': c['claim'], 'sentence': sentence,
                      'premise': ' '.join(verbalize(e) for e in cited), 'cited_ids': rec['answer']['cited_ids']})
    return items


def run_nli(name, rev, pairs):
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(name, revision=rev)
    model = AutoModelForSequenceClassification.from_pretrained(name, revision=rev).eval()
    labels = {int(k): v.lower() for k, v in model.config.id2label.items()}
    out = []
    with torch.no_grad():
        for p, h in pairs:
            enc = tok(p, h, truncation='only_first', max_length=512, return_tensors='pt')
            probs = torch.softmax(model(**enc).logits[0], -1).tolist()
            dist = {labels[j]: probs[j] for j in range(len(probs))}
            out.append({'supported': max(dist, key=dist.get) == 'entailment', 'p_entail': dist['entailment']})
    return out


def run_t5(name, rev, pairs):
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(name, revision=rev)
    model = AutoModelForSeq2SeqLM.from_pretrained(name, revision=rev).eval()
    yes, no = tok('yes').input_ids[0], tok('no').input_ids[0]
    out = []
    with torch.no_grad():
        for p, h in pairs:
            prompt = f'Evidence: {p}\nClaim: {h}\nIs the claim fully supported by the evidence? Answer yes or no.'
            enc = tok(prompt, truncation=True, max_length=512, return_tensors='pt')
            logits = model(**enc, decoder_input_ids=torch.tensor([[model.config.decoder_start_token_id]])).logits[0, -1]
            p_yes = torch.softmax(logits[[yes, no]], -1)[0].item()
            out.append({'supported': p_yes > 0.5, 'p_entail': p_yes})
    return out


def summarize(items, key):
    mis = [x for x in items if x['label'] in MISSTATED]
    cor = [x for x in items if x['label'] == 'correct']
    acc_m = sum(x[key]['supported'] for x in mis)
    acc_c = sum(x[key]['supported'] for x in cor)
    return {'misstated': len(mis), 'misstated_accepted': acc_m, 'correct': len(cor), 'correct_accepted': acc_c,
            'balanced_accuracy': round(0.5 * (acc_c / len(cor) + (len(mis) - acc_m) / len(mis)), 3)}


def write_table(saved, path):
    data = json.loads(saved.read_text())
    groups = lambda x: 'over' if x['label'] == 'overstated' else 'wrong'
    lines = [r'\begin{tabular}{@{}llrrrr@{}}', r'\toprule',
             r'Judge & Hyp. & Wrong & Over. & Correct & BA \\', r'\midrule']
    short = {'DeBERTa-v3-large (MNLI/FEVER/ANLI/LingNLI/WANLI)': 'DeBERTa-v3 (5 NLI sets)',
             'DeBERTa-v3-large (SNLI/MNLI cross-encoder)': 'DeBERTa-v3 (SNLI/MNLI)',
             'RoBERTa-large-MNLI': 'RoBERTa-large-MNLI', 'Flan-T5-large (yes/no)': 'Flan-T5-large'}
    for key, s in data['summary'].items():
        judge, hyp = key.split(' | ')
        mis = [x for x in data['items'] if x['label'] in MISSTATED]
        acc = {g: sum(x['judges'][key]['supported'] for x in mis if groups(x) == g) for g in ('wrong', 'over')}
        tot = {g: sum(groups(x) == g for x in mis) for g in ('wrong', 'over')}
        lines.append(f"{short[judge]} & {'sent.' if hyp == 'sentence' else 'claim'} & {acc['wrong']}/{tot['wrong']} & "
                     f"{acc['over']}/{tot['over']} & {s['correct_accepted']}/{s['correct']} & {s['balanced_accuracy']:.2f} \\\\")
    lines += [r'\bottomrule', r'\end{tabular}']
    path.write_text('\n'.join(lines) + '\n')
    print(f'wrote {path}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--tex', type=Path, help='only write the LaTeX table from the saved results')
    a = ap.parse_args()
    if a.tex:
        write_table(a.out, a.tex)
        return
    items = build_items()
    summary = {}
    if a.out.exists():  # resume: keep judges already scored
        prev = json.loads(a.out.read_text())
        summary = prev.get('summary', {})
        done = {x['id']: x.get('judges', {}) for x in prev.get('items', [])}
        for x in items:
            x['judges'] = done.get(x['id'], {})
    for label, name, rev, kind in JUDGES:
        for hyp in ('sentence', 'claim'):
            key = f'{label} | {hyp}'
            if key in summary:
                continue
            pairs = [(x['premise'], x[hyp]) for x in items]
            res = run_nli(name, rev, pairs) if kind == 'nli' else run_t5(name, rev, pairs)
            for x, r in zip(items, res):
                x.setdefault('judges', {})[key] = r
            summary[key] = summarize([dict(x, _=x['judges'][key]) for x in items], '_')
            s = summary[key]
            print(f"{key}: misstated accepted {s['misstated_accepted']}/{s['misstated']}, "
                  f"correct accepted {s['correct_accepted']}/{s['correct']}, balanced acc {s['balanced_accuracy']}",
                  flush=True)
            a.out.write_text(json.dumps({'judges': [{'label': l, 'model': n, 'revision': r} for l, n, r, _ in JUDGES],
                                         'definition': 'premise = verbalized cited evidence items; supported = '
                                                       'entailment (NLI argmax) or p(yes) > 0.5 (Flan-T5)',
                                         'summary': summary, 'items': items}, indent=2) + '\n')
    print(f'wrote {a.out}', flush=True)


if __name__ == '__main__':
    main()
