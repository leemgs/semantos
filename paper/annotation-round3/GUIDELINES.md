# Guidelines for the third annotator (two short tasks)

Thank you for helping. Please work **independently**: do not open any other
label file in the repository, and do not discuss items with the authors or
earlier annotators until you are done. Total time is about two hours.

Do **not** open `taskB-key.json`. It links rows to models and is only for
scoring.

---

## Task A: find the claims (about 60–75 minutes)

**File:** `taskA-explanations.csv` has 27 short explanations (`E01`–`E27`)
that language models wrote when recommending a Linux configuration.

**What to do:** for each explanation, list every **quantitative or
comparative statement about the evidence**. Write one row per claim in
`taskA-claims.csv` (start from `taskA-claims-template.csv` and delete its
example row). Each row has three columns:

- `expl_id`: for example `E07`.
- `span`: copy the **exact words** of the claim from the explanation. Copy
  enough words that the claim is clear; it need not be a full sentence.
- `note`: optional.

**What counts as one claim:**

- A stated value, range, minimum, maximum, average, count or unit, for example
  "ranges from 82.488 to 183.217".
- A comparison or ordering, for example "lower than any other config" or
  "consistently the lowest".
- A list of values counts as **one** claim. A comparison made about that list
  counts as a **separate** claim.
- Do not list the recommendation itself ("s50000_aall is the best choice"),
  restatements of the goal, or statements about the method.

You do not judge whether a claim is true in Task A, only whether it is a
claim. When in doubt, list it and add a note.

---

## Task B: check database explanations (about 30–45 minutes)

**Files:**

- `taskB-sqlite-blind.csv`: 27 explanations (`S01`–`S27`) recommending SQLite
  settings, with the configuration each recommends.
- `taskB-evidence.csv`: the exact evidence the models saw. All values are P95
  commit latencies in microseconds.
  - Training table: the mean P95 per configuration.
  - 40 retrieval runs: ten blocks, one run per configuration in each block.

**What to do:** for each row, fill in two columns with `yes` or `no`, and add
a note if you like:

- `contains_misstatement`: `yes` if the explanation states anything about the
  evidence that is false. That includes:
  - a wrong value, range, median or average;
  - a false comparison, for example a higher number called "lower";
  - a wrong unit;
  - "consistently", "always" or "all" when that holds only in most blocks;
  - "significant" (the evidence contains no statistical test).

  Rounding to the written precision is fine. If a statement is explicitly
  about some blocks or runs, judge it against those.
- `misreports_training_table`: `yes` only if the explanation misstates the
  **training table**, for example by calling a configuration the table's
  lowest when it is not.

Please note in `note` the words you judged wrong.

---

## When you are done

Return `taskA-claims.csv` and `taskB-sqlite.csv` (your filled copy of
`taskB-sqlite-blind.csv`). The authors will run:

```
python3 code/evaluation/blind_round3.py score --dir paper/annotation-round3
```

The authors will report agreement in the paper with your consent. You will
not be named in the anonymous version.
