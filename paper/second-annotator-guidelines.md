# Guidelines for the second annotator

Thank you for helping. You will label 97 short claims taken from explanations
that language models wrote when recommending a Linux configuration. Please
label **independently**: do not look at any other label file, and do not
discuss items with the first annotator until you have finished. It takes
about 60–90 minutes.

## Your file

`second-annotator-blind.csv`: one row per claim. Columns:

- `source_sentence`: the sentence the model wrote;
- `claim`: the specific quantitative or comparative claim in it to judge
  (when a sentence contains several claims, judge only this one);
- `evidence_supplied`: `no` means the model was given no evidence at all;
- `second_label`: **fill in** one label from the list below;
- `second_note`: optional comment.

## The evidence the models were given (all values are P95 latencies in microseconds)

- **Training table (mean per configuration):** s50000_aall 132.94;
  s50000_aone 277.46; s1000000_aall 954.76; s1000000_aone 1080.66.
- **Retrieval runs, 10 per configuration, in this order (blocks 0–9):**
  - s50000_aall: 126.36, 140.554, 94.81, 99.853, 93.049, 183.217, 109.519, 82.488, 87.387, 87.347
  - s50000_aone: 571.84, 272.927, 151.299, 254.509, 170.306, 430.654, 97.457, 89.789, 85.033, 150.643
  - s1000000_aall: minimum 748.404, maximum 1023.152, mean 953.05
  - s1000000_aone: minimum 817.997, maximum 1419.669, mean 1013.99
- **Per block, the lowest configuration** is s50000_aall in 8 of 10 blocks
  and s50000_aone in 2 (blocks 6 and 8).
- The configuration names are opaque labels; nothing in a name says which is
  better.

## Labels

| Label | Use when |
|---|---|
| `correct` | the claim is true of the evidence (rounding to the written precision is fine) |
| `overstated` | the claim states a regularity more strongly than the evidence supports, e.g. "consistently", "always", "in all runs" or "significantly" when it holds only in most cases or no test supports significance |
| `wrong` | a value, range, extremum or ordering is false |
| `partly wrong` | the claim combines a true and a false part |
| `wrong unit` | the number is right but the unit is wrong (e.g. ms instead of µs) |
| `wrong attribution` | a value is assigned to the wrong source (e.g. a retrieval run reported as the training mean) |
| `unsupported prior` | only when `evidence_supplied` is `no`: the claim relies on assumptions about the configuration names |

Rules: a list of values counts as one claim; a comparison counts as a
separate claim. If a claim talks about the runs the model cited, judge it
against those runs where the sentence makes that clear; otherwise judge it
against all the evidence.

## When you are done

Return the CSV. The authors will compute agreement with
`python3 code/evaluation/claim_review_agreement.py kappa --second second-annotator-blind.csv`
and report it in the paper with your consent (you will not be named in the
anonymous version).
