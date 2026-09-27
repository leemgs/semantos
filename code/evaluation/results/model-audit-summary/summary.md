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

## Qwen2.5-14B-Instruct-Q4_K_M

Weights SHA-256: `a09ea5e7b1eafb1b30b241726c3cc3c905c96f14ad41e246ffa5f44e53904f68`; runtime llama-cpp-python 0.3.35; seeds [4088, 4089, 4090, 4091, 4092]; 20/20 valid calls, 3136 s total (156.8 s/call).

| Variant | Valid/calls | Choices | Mean citations | Cites table | Cites graph | Quoted decimals in prompt |
|---|---|---|---|---|---|---|
| full | 5/5 | {'s50000_aall': 5} | 6.0 | 5 | 0 | 5/5 |
| no_graph | 5/5 | {'s50000_aall': 5} | 6.0 | 5 | 0 | 15/15 |
| no_retrieval | 5/5 | {'s50000_aall': 5} | 2.0 | 5 | 5 | 5/5 |
| model_only | 5/5 | {'s50000_aone': 5} | 0.0 | 0 | 0 | 0/0 |

Probe (exploratory post hoc probe; not part of the preregistered audit): delete_cited -> s50000_aone (changed: True); delete_control -> s50000_aall (changed: False).

Faithfulness: 0 estimable seeds, 5 not estimable; action changed after deleting cited context in 0, after deleting matched uncited context in 0.

| Chosen config | Period ms | Test P95 us ± 95% CI | Paired reduction % ± 95% CI |
|---|---|---|---|
| s50000_aall | 5 | 179.7 ± 102.0 | 0.0 ± 0.0 |
| s50000_aall | 8 | 155.7 ± 64.4 | 0.0 ± 0.0 |
| s50000_aone | 5 | 344.2 ± 123.0 | -145.0 ± 125.2 |
| s50000_aone | 8 | 390.5 ± 183.3 | -179.8 ± 155.6 |

## phi-4-Q4_K

Weights SHA-256: `5652b9be0ea4ae2842130d04fe31bc869fcb99a2b7106c53b4e754a343fd688f`; runtime llama-cpp-python 0.3.35; seeds [4088, 4089, 4090, 4091, 4092]; 30/30 valid calls, 4516 s total (150.5 s/call).

| Variant | Valid/calls | Choices | Mean citations | Cites table | Cites graph | Quoted decimals in prompt |
|---|---|---|---|---|---|---|
| full | 5/5 | {'s50000_aall': 5} | 6.0 | 0 | 0 | 30/30 |
| no_graph | 5/5 | {'s50000_aall': 5} | 6.0 | 0 | 0 | 30/30 |
| no_retrieval | 5/5 | {'s50000_aall': 5} | 1.0 | 5 | 0 | 25/25 |
| model_only | 5/5 | {'s1000000_aone': 5} | 0.0 | 0 | 0 | 0/0 |
| delete_cited | 5/5 | {'s50000_aone': 5} | 6.0 | 0 | 0 | 30/30 |
| delete_uncited | 5/5 | {'s50000_aall': 5} | 6.0 | 0 | 0 | 30/30 |

Probe (exploratory post hoc probe; not part of the preregistered audit): delete_cited -> s50000_aone (changed: True); delete_control -> s50000_aall (changed: False).

Faithfulness: 5 estimable seeds, 0 not estimable; action changed after deleting cited context in 5, after deleting matched uncited context in 0.

| Chosen config | Period ms | Test P95 us ± 95% CI | Paired reduction % ± 95% CI |
|---|---|---|---|
| s50000_aall | 5 | 179.7 ± 102.0 | 0.0 ± 0.0 |
| s50000_aall | 8 | 155.7 ± 64.4 | 0.0 ± 0.0 |
| s1000000_aone | 5 | 1023.3 ± 29.9 | -631.2 ± 182.7 |
| s1000000_aone | 8 | 1041.6 ± 68.1 | -699.0 ± 206.4 |
| s50000_aone | 5 | 344.2 ± 123.0 | -145.0 ± 125.2 |
| s50000_aone | 8 | 390.5 ± 183.3 | -179.8 ± 155.6 |

## meta-llama/llama-3.3-70b-instruct

Hosted via openrouter (weights not hashable); reported models ['meta-llama/llama-3.3-70b-instruct'], routed providers ['AkashML', 'DeepInfra', 'Parasail'], fingerprints ['None']; seeds [4088, 4089, 4090, 4091, 4092]; 30/30 valid calls, 593 s total (19.8 s/call).

| Variant | Valid/calls | Choices | Mean citations | Cites table | Cites graph | Quoted decimals in prompt |
|---|---|---|---|---|---|---|
| full | 5/5 | {'s50000_aall': 5} | 5.6 | 0 | 0 | 12/12 |
| no_graph | 5/5 | {'s50000_aall': 5} | 6.0 | 0 | 0 | 10/10 |
| no_retrieval | 5/5 | {'s50000_aall': 5} | 1.0 | 5 | 0 | 5/5 |
| model_only | 5/5 | {'s1000000_aone': 5} | 0.0 | 0 | 0 | 0/0 |
| delete_cited | 5/5 | {'s50000_aall': 5} | 3.0 | 0 | 0 | 15/15 |
| delete_uncited | 5/5 | {'s50000_aall': 5} | 6.0 | 0 | 0 | 21/21 |

Probe (exploratory post hoc probe; not part of the preregistered audit): delete_cited -> s50000_aall (changed: False); delete_control -> s50000_aall (changed: False).

Faithfulness: 5 estimable seeds, 0 not estimable; action changed after deleting cited context in 0, after deleting matched uncited context in 0.

| Chosen config | Period ms | Test P95 us ± 95% CI | Paired reduction % ± 95% CI |
|---|---|---|---|
| s50000_aall | 5 | 179.7 ± 102.0 | 0.0 ± 0.0 |
| s50000_aall | 8 | 155.7 ± 64.4 | 0.0 ± 0.0 |
| s1000000_aone | 5 | 1023.3 ± 29.9 | -631.2 ± 182.7 |
| s1000000_aone | 8 | 1041.6 ± 68.1 | -699.0 ± 206.4 |

## qwen/qwen3-235b-a22b-2507

Hosted via openrouter (weights not hashable); reported models ['qwen/qwen3-235b-a22b-2507'], routed providers ['DeepInfra', 'GMICloud', 'Nebius', 'Novita'], fingerprints ['None', 'vllm-v0.22.0-tp4-8006095a']; seeds [4088, 4089, 4090, 4091, 4092]; 29/30 valid calls, 241 s total (8.0 s/call).

| Variant | Valid/calls | Choices | Mean citations | Cites table | Cites graph | Quoted decimals in prompt |
|---|---|---|---|---|---|---|
| full | 5/5 | {'s50000_aall': 5} | 6.0 | 0 | 0 | 20/20 |
| no_graph | 5/5 | {'s50000_aall': 5} | 6.0 | 0 | 0 | 15/15 |
| no_retrieval | 5/5 | {'s50000_aall': 5} | 1.0 | 5 | 0 | 8/8 |
| model_only | 5/5 | {'s1000000_aone': 3, 's50000_aall': 1, 's50000_aone': 1} | 0.0 | 0 | 0 | 0/0 |
| delete_cited | 4/5 | {'s50000_aall': 4} | 4.0 | 0 | 0 | 22/22 |
| delete_uncited | 5/5 | {'s50000_aall': 5} | 6.0 | 0 | 0 | 15/15 |

Probe (exploratory post hoc probe; not part of the preregistered audit): delete_cited -> s50000_aall (changed: False); delete_control -> s50000_aall (changed: False).

Faithfulness: 4 estimable seeds, 0 not estimable; action changed after deleting cited context in 0, after deleting matched uncited context in 0.

| Chosen config | Period ms | Test P95 us ± 95% CI | Paired reduction % ± 95% CI |
|---|---|---|---|
| s50000_aall | 5 | 179.7 ± 102.0 | 0.0 ± 0.0 |
| s50000_aall | 8 | 155.7 ± 64.4 | 0.0 ± 0.0 |
| s1000000_aone | 5 | 1023.3 ± 29.9 | -631.2 ± 182.7 |
| s1000000_aone | 8 | 1041.6 ± 68.1 | -699.0 ± 206.4 |
| s50000_aone | 5 | 344.2 ± 123.0 | -145.0 ± 125.2 |
| s50000_aone | 8 | 390.5 ± 183.3 | -179.8 ± 155.6 |

## deepseek/deepseek-v3.2

Hosted via openrouter (weights not hashable); reported models ['deepseek/deepseek-v3.2'], routed providers ['Alibaba', 'AtlasCloud', 'Baidu', 'DeepInfra'], fingerprints ['None']; seeds [4088, 4089, 4090, 4091, 4092]; 20/20 valid calls, 102 s total (5.1 s/call).

| Variant | Valid/calls | Choices | Mean citations | Cites table | Cites graph | Quoted decimals in prompt |
|---|---|---|---|---|---|---|
| full | 5/5 | {'s50000_aall': 5} | 6.0 | 5 | 0 | 45/45 |
| no_graph | 5/5 | {'s50000_aall': 5} | 6.0 | 0 | 0 | 32/36 |
| no_retrieval | 5/5 | {'s50000_aall': 5} | 2.0 | 5 | 5 | 6/6 |
| model_only | 5/5 | {'s50000_aone': 5} | 0.0 | 0 | 0 | 0/0 |

Probe (exploratory post hoc probe; not part of the preregistered audit): delete_cited -> s50000_aall (changed: False); delete_control -> s50000_aall (changed: False).

Faithfulness: 0 estimable seeds, 5 not estimable; action changed after deleting cited context in 0, after deleting matched uncited context in 0.

| Chosen config | Period ms | Test P95 us ± 95% CI | Paired reduction % ± 95% CI |
|---|---|---|---|
| s50000_aall | 5 | 179.7 ± 102.0 | 0.0 ± 0.0 |
| s50000_aall | 8 | 155.7 ± 64.4 | 0.0 ± 0.0 |
| s50000_aone | 5 | 344.2 ± 123.0 | -145.0 ± 125.2 |
| s50000_aone | 8 | 390.5 ± 183.3 | -179.8 ± 155.6 |

Valid outputs and unchanged choices are not an LLM advantage; five seeds under greedy decoding are not independent samples.
