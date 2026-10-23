# Author verification sheet: AI-assisted readings (Appendices J and K)

An AI assistant made these readings, and the paper reports them as unverified. An author or annotator should
tick each item after checking it against the evidence; the paper can then say the readings were verified.
Evidence facts for the SQLite task: training table sync_off_wal 71.652 us, sync_normal_wal 99.496 us;
sync_normal_wal retrieval runs 41.329-114.05 us (block 3 = 114.05), mean 61.69, median 46.133; it is lowest in 8 of 10 blocks.

## Appendix K (SQLite): 13 explanations with an issue

| ok? | model, seed | issue | note |
|---|---|---|---|
| [ ] | Qwen3-235B 4089 | overstated | "consistently achieves the lowest" (lowest in 8 of 10 blocks) |
| [ ] | Qwen3-235B 4090 | table misreported | says sync_normal_wal (99.496) is lowest in the training summary; sync_off_wal is 71.652 |
| [ ] | Qwen3-235B 4091 | wrong range; overstated | range 41.329-102.838 (all runs 41.329-114.05; cited runs 43.456-114.05); "consistently ... lowest" |
| [ ] | Qwen3-235B 4092 | table misreported; wrong unit; overstated | says 99.496 performs better than sync_off_wal (71.652); table values given in ms; "consistently ... lowest" |
| [ ] | DeepSeek-V3.2 4088 | overstated | "consistently show ... the lowest P95 latencies among all configs" (8 of 10 blocks) |
| [ ] | DeepSeek-V3.2 4090 | table misreported | says the training summary gives sync_normal_wal the lowest average (99.5); sync_off_wal is 71.652 |
| [ ] | DeepSeek-V3.2 4091 | overstated | "consistently show ... the lowest P95 latencies among all configs" |
| [ ] | DeepSeek-V3.2 4092 | table misreported | says the training summary gives sync_normal_wal the lowest average (99.496) |
| [ ] | Nemotron-3-Ultra-550B 4088 | table misreported; wrong range | "lowest ... across both training and retrieval evidence" while quoting 99.496 vs 71.652; blocks 0-4 of sync_normal_wal given as 41-54 (43.456-114.05) |
| [ ] | Nemotron-3-Ultra-550B 4089 | table misreported; wrong range | as 4088; blocks 0-4 of sync_normal_wal given as 43-54 (block 3 is 114.05) |
| [ ] | Nemotron-3-Ultra-550B 4090 | table misreported | 99.496 "significantly lower than sync_off_wal (71.652)" |
| [ ] | Nemotron-3-Ultra-550B 4091 | table misreported | 99.496 "significantly lower than sync_off_wal (71.652)" |
| [ ] | Nemotron-3-Ultra-550B 4092 | table misreported; wrong range; wrong value | "lowest across both training and retrieval"; blocks 0-4 given as 43-54; median given as 43.8 (46.133) |

The 14 explanations read as having no issue are also listed in `code/evaluation/results/domain-sqlite/explanations-read.csv`.

## Appendix J (evidence instances): range-check flags read by the assistant

| ok? | item | reading |
|---|---|---|
| [ ] | I1 Llama-3.3-70B 4089, 4092 | s50000_aone range 76.186-148.876 / 76.186-697.378 is wrong (max 705.847) |
| [ ] | I1 Nemotron 4088, 4089 | s50000_aall range 85.9-129.5 is wrong (it reaches 312.316) |
| [ ] | I1 Nemotron 4091 | s50000_aone 76-697 is wrong (max 705.8); "~85-130" for s50000_aall contradicts its own list (312.316) |
| [ ] | I1 Gemini Flash 4091 | "~85-102 across most runs" is acceptable (7 of 10 runs) |
| [ ] | I3 Nemotron 4088, 4090, 4092 | s50000_aone "466.089-152.215" gives two run values, not the range (91.943-466.089) |
| [ ] | I3 Nemotron 4089 | "~900-1500" for s1000000 is an acceptable approximation (924.3-1521.0) |
| [ ] | I3 Llama-3.3-70B 4088-4092 | computed mean given as 93.3188 / 93.3392 / 93.39; actual 93.339 |

After verification, change "read ... with an AI assistant; the reading has not been independently verified" in
Appendices J and K and in Use of AI assistants to state who verified the readings.
