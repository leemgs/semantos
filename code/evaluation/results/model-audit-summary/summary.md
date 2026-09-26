# Model audit summary

Retrospective frozen-input selection audit on the controlled follow-up. Prompts contain
training and retrieval evidence only; held-out outcomes are read after all calls.

## Qwen2.5-7B-Instruct-Q4_K_M

Weights SHA-256: `dfce12e3862a5283ccfb88221b48480e58745165de856439950d0f22590580db`; runtime llama-cpp-python 0.3.35; seeds [4088, 4089, 4090, 4091, 4092]; 20/20 valid calls, 1603 s total (80.2 s/call).

| Variant | Valid/calls | Choices | Mean citations | Cites table | Cites graph | Quoted decimals in prompt |
|---|---|---|---|---|---|---|
| full | 5/5 | {'s50000_aall': 5} | 6.0 | 5 | 0 | 5/5 |
| no_graph | 5/5 | {'s50000_aall': 5} | 6.0 | 5 | 0 | 5/5 |
| no_retrieval | 5/5 | {'s50000_aall': 5} | 1.0 | 5 | 0 | 5/5 |
| model_only | 5/5 | {'s50000_aone': 5} | 0.0 | 0 | 0 | 0/0 |

Probe (exploratory post hoc probe; not part of the preregistered audit): delete_cited -> s50000_aone (changed: True); delete_control -> s50000_aall (changed: False).

Faithfulness: 0 estimable seeds, 5 not estimable; action changed after deleting cited context in 0, after deleting matched uncited context in 0.

| Chosen config | Period ms | Test P95 us ± 95% CI | Paired reduction % ± 95% CI |
|---|---|---|---|
| s50000_aall | 5 | 179.7 ± 102.0 | 0.0 ± 0.0 |
| s50000_aall | 8 | 155.7 ± 64.4 | 0.0 ± 0.0 |
| s50000_aone | 5 | 344.2 ± 123.0 | -145.0 ± 125.2 |
| s50000_aone | 8 | 390.5 ± 183.3 | -179.8 ± 155.6 |

## Meta-Llama-3.1-8B-Instruct-Q4_K_M

Weights SHA-256: `7b064f5842bf9532c91456deda288a1b672397a54fa729aa665952863033557c`; runtime llama-cpp-python 0.3.35; seeds [4088, 4089, 4090, 4091, 4092]; 30/30 valid calls, 2325 s total (77.5 s/call).

| Variant | Valid/calls | Choices | Mean citations | Cites table | Cites graph | Quoted decimals in prompt |
|---|---|---|---|---|---|---|
| full | 5/5 | {'s50000_aone': 5} | 6.0 | 0 | 0 | 5/5 |
| no_graph | 5/5 | {'s50000_aone': 5} | 6.0 | 0 | 0 | 5/5 |
| no_retrieval | 5/5 | {'s50000_aone': 5} | 1.0 | 5 | 0 | 5/5 |
| model_only | 5/5 | {'s50000_aone': 5} | 0.0 | 0 | 0 | 0/0 |
| delete_cited | 5/5 | {'s1000000_aall': 5} | 6.0 | 0 | 0 | 5/5 |
| delete_uncited | 5/5 | {'s50000_aall': 5} | 6.0 | 5 | 0 | 5/5 |

Probe (exploratory post hoc probe; not part of the preregistered audit): delete_cited -> s1000000_aall (changed: True); delete_control -> s50000_aall (changed: True).

Faithfulness: 5 estimable seeds, 0 not estimable; action changed after deleting cited context in 5, after deleting matched uncited context in 5.

| Chosen config | Period ms | Test P95 us ± 95% CI | Paired reduction % ± 95% CI |
|---|---|---|---|
| s50000_aone | 5 | 344.2 ± 123.0 | -145.0 ± 125.2 |
| s50000_aone | 8 | 390.5 ± 183.3 | -179.8 ± 155.6 |
| s1000000_aall | 5 | 973.9 ± 56.9 | -598.8 ± 188.2 |
| s1000000_aall | 8 | 961.9 ± 72.5 | -631.0 ± 179.1 |
| s50000_aall | 5 | 179.7 ± 102.0 | 0.0 ± 0.0 |
| s50000_aall | 8 | 155.7 ± 64.4 | 0.0 ± 0.0 |

Valid outputs and unchanged choices are not an LLM advantage; five seeds under greedy decoding are not independent samples.
