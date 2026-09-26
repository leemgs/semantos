# Controlled per-thread experiment

single shared host, one periodic workload family; period-disjoint roles, no host/family holdout

Policy comparisons are offline replay on the same held-out grid, not live LLM execution.

| Period ms | Policy | P95 us ± 95% CI | Paired reduction % ± 95% CI | Misses/events |
|---|---|---|---|---|
| 5 | control | 179.7 ± 102.0 | 0.0 ± 0.0 | 13/400 |
| 5 | empirical_min | 179.7 ± 102.0 | 0.0 ± 0.0 | 13/400 |
| 5 | graph_min | 179.7 ± 102.0 | 0.0 ± 0.0 | 13/400 |
| 5 | seeded_random | 811.6 ± 230.2 | -499.0 ± 248.2 | 248/400 |
| 8 | control | 155.7 ± 64.4 | 0.0 ± 0.0 | 13/400 |
| 8 | empirical_min | 155.7 ± 64.4 | 0.0 ± 0.0 | 13/400 |
| 8 | graph_min | 155.7 ± 64.4 | 0.0 ± 0.0 | 13/400 |
| 8 | seeded_random | 642.2 ± 330.2 | -355.2 ± 277.9 | 225/400 |

Safety replay (TP=veto unsafe; FP=veto safe; FN=accept unsafe; TN=accept safe):

| Period | alpha | tau | TP | FP | FN | TN |
|---|---|---|---|---|---|---|
| 5 | 0.05 | 0.922 | 20 | 0 | 5 | 15 |
| 5 | 0.1 | 0.922 | 20 | 0 | 5 | 15 |
| 5 | 0.2 | 0.922 | 20 | 0 | 5 | 15 |
| 8 | 0.05 | 0.922 | 20 | 0 | 4 | 16 |
| 8 | 0.1 | 0.922 | 20 | 0 | 4 | 16 |
| 8 | 0.2 | 0.922 | 20 | 0 | 4 | 16 |

Actual staged executions:

| Period | Applied | Completed | Stopped/restored | Total restored | Misses/events |
|---|---|---|---|---|---|
| 5 | 40 | 7 | 33 | 40 | 186/816 |
| 8 | 40 | 7 | 33 | 40 | 190/880 |

No recovery deadline, rollback precision, host-generalization or LLM advantage is inferred.
Student-t intervals are descriptive across ten shared-host blocks; no multiplicity correction.
Costs and complete traces are in analysis.json and decision-traces.jsonl.
