# Human-impact study: pre-registration protocol (draft, not yet run)

Status: **materials ready, no data collected.** Nothing in this folder is a result.
The paper reports no human-impact measurement. Results may be added only after
real participants have taken part under an approved protocol.

## Question

The audit found that most misstated explanations accompany a correct decision
(Section 5.3). Does such a rationale change what a reader believes the evidence
shows, even when the decision and citations are right? Does the reader notice?

## Hypotheses (directional, fixed before data collection)

- **H1 (primary).** Participants who read the misstated rationale (M) answer the
  probes that rationale misstates (targeted probes) less accurately than
  participants who read the minimally corrected rationale (C).
- **H1b.** Targeted accuracy under M is lower than with no rationale (N).
- **H2 (secondary, two-sided).** Trust ratings differ between M and C. We expect
  no clear difference, because the errors are not visible without checking.
- **H3 (descriptive).** We report the share of participants who open the
  measurements, by condition, and targeted accuracy split by whether they opened them.

## Design

- **Between subjects:** 3 conditions (M, C, N) x 6 stimuli (S1-S6). Each
  participant sees one advisor brief.
- **Assignment.** The researcher gives each participant a sequential assignment
  number k. The condition is `["M","C","N"][k % 3]` and the stimulus is
  `S[(k // 3) % 6]`, so conditions stay balanced within each stimulus.
- **Stimuli.** Each stimulus is the verbatim full-context explanation of one
  hosted model run. All recommend s50000_aall, the correct choice. Each brief
  shows the model's own citations.

  | Stimulus | Source model | Seed | What it misstates | Targeted probes |
  |---|---|---|---|---|
  | S1 | Nemotron-550B | 4089 | "consistently lowest across all runs"; s50000_aone range 85.0-430.7 (true max 571.84) | P1, P5 |
  | S2 | DeepSeek-V3.2 | 4089 | max 183.217 "lower than the lowest of any other config" (s50000_aone min 85.033) | P2 |
  | S3 | DeepSeek-V3.2 | 4088 | "consistently lowest"; "both s1000000 consistently above 800" (min 748.404) | P3, P5 |
  | S4 | Llama-3.3-70B | 4089 | range 82.488-140.554 (true max 183.217) | P4 |
  | S5 | Qwen3-235B | 4088 | "consistently lowest"; "all other configurations significantly higher" (no test; ranges overlap) | P5, P6 |
  | S6 | Gemini-3.1-Pro | 4090 | "consistently achieves the lowest" (8 of 10 blocks) | P5 |

  These errors match the human-verified labels in
  `code/evaluation/results/model-audit-summary/claim-audit.json`. The script
  re-checks every probe answer against the frozen evidence. S1 and S5 were
  truncated by the token limit, so they end at the last complete sentence. For
  S5 the cut final sentence is completed with its evident ending ("latency.").
- **Corrected rationales (C)** change only the misstated phrases. They were
  drafted with an AI assistant. **Before data collection, an author must check
  every C text against the evidence and sign off below.**
- **Probes** are six yes/no questions about the measurements, the same for every
  participant. "Not sure" counts as incorrect.

  | Probe | Question | Answer |
  |---|---|---|
  | P1 | Is the highest s50000_aone run above 500 us? | yes (571.84) |
  | P2 | Does any run of another configuration fall below the highest s50000_aall run? | yes (85.033 < 183.217) |
  | P3 | Is every s1000000 run above 800 us? | no (748.404) |
  | P4 | Is the highest s50000_aall run above 150 us? | yes (183.217) |
  | P5 | Is s50000_aall lowest in all ten blocks? | no (8 of 10) |
  | P6 | Does the evidence report a significance test? | no |

- **Other measures:**
  - trust in the brief (1-7);
  - whether and when the participant opened the measurements, logged by the instrument;
  - completion time;
  - one instructed-response attention item.

## Participants

- Adults who can read technical English. Include engineers or computer science
  students if possible, because they are the intended users of such advice.
- **Sample size: 60 per condition after exclusions (180 in total).** Recruit
  about 200.
- Power was estimated by simulation (`python3 human_study.py power`). The
  assumptions are 80% targeted accuracy under C and N, 55% under M, and a
  participant SD of 1.0 on the logit scale. Under these assumptions, 60 per arm
  gives power ≈ 0.85 for H1 at one-sided α = .05 (50 per arm ≈ 0.78; 70 per
  arm ≈ 0.90). These are assumptions, not data. If a pilot gives different
  rates, update the sample size before the main study and record the change.
- Pilot: about 10 participants, used only to check that the instructions are
  understood. Pilot data are excluded from the analysis.

## Procedure (about 10 minutes)

1. Information sheet and consent (`consent.md`).
2. The participant opens `instrument.html` and enters the participant code and
   assignment number given by the researcher. No names or contact details are
   entered.
3. Task description, then the advisor brief. The measurements are available
   behind a button, and opening them is logged.
4. Six probes, the trust rating and the attention item.
5. Debriefing: the brief was written by a language model, some briefs misstate
   the measurements, and the correct answers are shown. The participant saves
   the response file and returns it to the researcher.

The instrument is a static page. It sends nothing over the network. It can also
be rebuilt in a survey platform with the same texts from `stimuli.json`.

## Exclusions (fixed in advance)

- Failed attention item.
- Incomplete response.
- Completion under 60 seconds.
- Duplicate participant code (keep the first).

## Analysis (`python3 human_study.py analyze --responses responses.csv`)

- **Primary (H1).** For each participant, compute the proportion of targeted
  probes answered correctly. Compare M with C using a one-sided permutation test
  of the difference in means, with condition labels permuted within stimulus.
  Use 20,000 permutations and α = .05.
- **H1b.** The same test for M against N.
- **H2.** The same permutation test on trust, two-sided.
- **Secondary.**
  - Probe-level GEE logistic regression (exchangeable correlation within
    participant, stimulus fixed effects).
  - Untargeted-probe accuracy as a check that conditions do not differ in general
    attention.
- **H3.** Descriptive only.
- No other confirmatory tests. Anything else is labeled exploratory.

## Ethics

- Minimal risk.
- No personal data. Responses are tied only to a researcher-assigned code.
- Participants learn after the task that some briefs contain errors. This is a
  mild form of non-disclosure, which the debriefing resolves.
- Ethics review or exemption must be obtained from the researchers'
  institution before recruitment. Compensation follows that institution's rules
  and local minimum-wage standards.
- If the study is run, the paper's Ethics statement must be updated: it
  currently says the work involves no human participants beyond the volunteer
  annotators.

## Sign-off before data collection

- [ ] An author checked the six C rationales against the evidence.
- [ ] An author checked the probe answers against the evidence.
- [ ] Ethics approval or exemption obtained (reference: ______).
- [ ] Protocol registered (e.g., OSF or AsPredicted) on ______, before the first participant.
