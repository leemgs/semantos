# 주장 라벨 검토: 집중 검토 41행

`claim-label-review.csv`에서 자동 검사 규칙으로 판정할 수 없어 사람의 판단이 필요한 41행입니다. 각 항목마다
(1) 모델이 실제로 쓴 문장, (2) AI가 붙인 라벨과 근거, (3) 판단에 필요한 근거 수치를 함께 적었습니다.

**하실 일:** 각 항목에서 라벨이 맞으면 아무것도 하지 않습니다. 틀리면 `claim-label-review.csv`의 같은 `id` 행 `reviewer_label` 칸에 올바른 라벨을 적습니다
(correct / overstated / wrong / partly wrong / wrong unit / wrong attribution / unsupported prior). 필요하면 `reviewer_note`에 이유를 적습니다.

**근거 수치 요약 (단위 µs):** s50000_aall 10개 run = 126.36, 140.554, 94.81, 99.853, 93.049, 183.217, 109.519, 82.488, 87.387, 87.347 (최소 82.488, 최대 183.217, 평균 110.5) · s50000_aone 10개 run = 571.84, 272.927, 151.299, 254.509, 170.306, 430.654, 97.457, 89.789, 85.033, 150.643 (최소 85.033, 최대 571.84) · s1000000_aall 최소 748.404, 최대 1023.152 · s1000000_aone 최소 817.997, 최대 1419.669 · training 평균: aall 132.94, aone 277.46, 1ms-all 954.76, 1ms-one 1080.66 · block별 최저: aall 8/10, aone 2/10.

### id 1 · Qwen2.5-7B · full

- **모델 문장:** “Based on the training summaries and retrieval runs provided, the configuration 's50000_aall' has the lowest P95 latency for periodic wake-ups. … Additionally, the retrieval runs consistently show that 's50000_aall' has the lowest P95 latency across various”
- **추출된 주장:** retrieval runs consistently show s50000_aall lowest
- **AI 라벨:** `overstated` — 근거: lowest in 8 of 10 retrieval blocks
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 7 · Llama-3.1-8B · no_graph

- **모델 문장:** “The config 's50000_aone' has the lowest average P95 latency across all retrieval runs, with an average of 272.927 us.”
- **추출된 주장:** lowest average across retrieval runs, 272.927 us
- **AI 라벨:** `wrong` — 근거: 272.927 is one run; mean is 227.446 versus 110.458 for s50000_aall
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 8 · Llama-3.1-8B · no_retrieval

- **모델 문장:** “Based on the provided evidence, the configuration 's50000_aone' has the lowest measured training summary value of 277.4647, indicating the lowest periodic wake-up P95 latency.”
- **추출된 주장:** lowest training summary value, 277.4647
- **AI 라벨:** `wrong` — 근거: 132.9413 (s50000_aall) is lower
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 13 · Qwen2.5-14B · full

- **모델 문장:** “Based on the provided evidence, the configuration 's50000_aall' has the lowest P95 latency across all retrieval runs. … The retrieval runs also consistently show lower P95 latencies for 's50000_aall' compared to the other configurations.”
- **추출된 주장:** s50000_aall has the lowest P95 across all retrieval runs
- **AI 라벨:** `overstated` — 근거: lowest in 8 of 10 retrieval blocks
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 15 · Qwen2.5-14B · no_graph

- **모델 문장:** “According to the training summary table, 's50000_aall' has a P95 latency of 132.9413 ms. … Additionally, the retrieval runs show that 's50000_aall' consistently has the lowest P95 latency across multiple runs, with the highest being 183.217 ms and the lowest being 82.488 ms.”
- **추출된 주장:** s50000_aall retrieval runs range from 82.488 to 183.217
- **AI 라벨:** `correct` — 근거: matches minimum and maximum
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 19 · Phi-4 · full

- **모델 문장:** “The P95 latencies for 's50000_aall' are 126.36, 140.554, 94.81, 99.853, 93.049, and 183.217 microseconds, which are significantly lower than those of the other configurations.”
- **추출된 주장:** these are significantly lower than those of the other configurations
- **AI 라벨:** `overstated` — 근거: s50000_aone runs 85.0-97.5 are below 126.36 and 183.217
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 21 · Phi-4 · no_graph

- **모델 문장:** “The P95 latencies for 's50000_aall' are 126.36, 140.554, 94.81, 99.853, 93.049, and 183.217 microseconds, which are significantly lower than those of the other configurations.”
- **추출된 주장:** these are significantly lower than those of the other configurations
- **AI 라벨:** `overstated` — 근거: s50000_aone runs 85.0-97.5 are below 126.36 and 183.217
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 25 · Phi-4 · delete_cited

- **모델 문장:** “The P95 latencies for 's50000_aone' are 571.84, 272.927, 151.299, 254.509, 170.306, and 430.654 microseconds, which are significantly lower than those of the other configurations.”
- **추출된 주장:** these are significantly lower than those of the other configurations
- **AI 라벨:** `wrong` — 근거: remaining s50000_aall runs are 82.488-109.519
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 27 · Phi-4 · delete_uncited

- **모델 문장:** “The P95 latencies for 's50000_aall' are 126.36, 140.554, 94.81, 99.853, 93.049, and 183.217 microseconds, which are significantly lower than those of the other configurations.”
- **추출된 주장:** these are significantly lower than those of other configurations
- **AI 라벨:** `overstated` — 근거: remaining s50000_aone runs 97.5-254.5 overlap 126.36-183.217
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 33 · Llama-3.3-70B · full

- **모델 문장:** “The config 's50000_aall' has the lowest average p95 latency across multiple retrieval runs (e.g., 'retrieval-3-2-s50000_aall', 'retrieval-3-3-s50000_aall', 'retrieval-3-4-s50000_aall', 'retrieval-3-7-s50000_aall', 'retrieval-3-8-s50000_aall', 'retrieval-3-9-s50000_aall') with values ranging from 82.488 to 126.36, indicating a more consistent and lower periodic wake-up P95 latency compared to other”
- **추출된 주장:** cited s50000_aall values range from 82.488 to 126.36
- **AI 라벨:** `wrong` — 근거: the six cited runs span 82.488-99.853
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 36 · Qwen3-235B · full

- **모델 문장:** “Among all configurations, 's50000_aall' consistently shows the lowest P95 latency across multiple retrieval runs (e.g., 126.36 us, 140.554 us, 94.81 us, etc.), with the highest observed P95 being 183.217 us. … In contrast, all other configurations (including 's50000_aone', 's1000000_aall', and 's1000000_aone') exhibit significantly higherP”
- **추출된 주장:** all other configurations exhibit significantly higher P95
- **AI 라벨:** `overstated` — 근거: s50000_aone runs 85.0-97.5 are below several s50000_aall runs
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 38 · Qwen3-235B · full

- **모델 문장:** “Among all configurations, 's50000_aall' consistently shows the lowest P95 latency across multiple retrieval runs (e.g., 126.36 us, 140.554 us, 94.81 us, etc.), with the highest observed P95 being 183.217 us. … In contrast, all other configurations (including 's50000_aone', 's1000000_aall', and 's1000000_aone') exhibit significantly higherP”
- **추출된 주장:** all other configurations exhibit significantly higher P95
- **AI 라벨:** `overstated` — 근거: s50000_aone runs 85.0-97.5 are below several s50000_aall runs
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 40 · Qwen3-235B · full

- **모델 문장:** “Among all configurations, 's50000_aall' consistently shows the lowest P95 latency across multiple retrieval runs (e.g., 126.36 us, 140.554 us, 94.81 us, etc.), with the highest observed P95 being 183.217 us. … In contrast, all other configurations (including 's50000_aone', 's1000000_aall', and 's1000000_aone') exhibit significantly higherP”
- **추출된 주장:** all other configurations exhibit significantly higher P95
- **AI 라벨:** `overstated` — 근거: s50000_aone runs 85.0-97.5 are below several s50000_aall runs
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 41 · DeepSeek-V3.2 · full

- **모델 문장:** “Among all retrieval runs, s50000_aall consistently shows the lowest P95 latencies across multiple trials (e.g., 126.36 μs, 140.554 μs, 94.81 μs, 99.853 μs, 93.049 μs), with most values under 150 μs. … Therefore, s50000_aall is the clear choice for minimizing P95 latency based on the retrieval run evidence.”
- **추출된 주장:** s50000_aall runs 126.36, 140.554, 94.81, 99.853, 93.049
- **AI 라벨:** `correct` — 근거: runs 0-4
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 42 · DeepSeek-V3.2 · full

- **모델 문장:** “In contrast, s50000_aone shows higher variability and often higher latencies (e.g., 571.84 μs, 272.927 μs), while both s1000000 configurations are consistently above 800 μs. … Therefore, s50000_aall is the clear choice for minimizing P95 latency based on the retrieval run evidence.”
- **추출된 주장:** s50000_aone often higher, e.g. 571.84, 272.927
- **AI 라벨:** `correct` — 근거: runs 0-1
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 45 · DeepSeek-V3.2 · full

- **모델 문장:** “For s50000_aall, the retrieval P95 values range from 82.488 µs to 183.217 µs across 10 runs, consistently lower than any retrieval values for s1000000_aall (748.404 µs to 1023.152 µs), s1000000_aone (817.997 µs to 1419.669 µs), and s50000_aone (85.033 µs to 571.84 µs). … Therefore, s50000_aall minimizes the periodic wake-up P95 latency based on the available evidence.”
- **추출된 주장:** s50000_aall runs range 82.488-183.217 us
- **AI 라벨:** `correct` — 근거: minimum and maximum
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 46 · DeepSeek-V3.2 · full

- **모델 문장:** “For s50000_aall, the retrieval P95 values range from 82.488 µs to 183.217 µs across 10 runs, consistently lower than any retrieval values for s1000000_aall (748.404 µs to 1023.152 µs), s1000000_aone (817.997 µs to 1419.669 µs), and s50000_aone (85.033 µs to 571.84 µs). … While s50000_aone occasionally has low retrieval values (e.g., 85.033 µs), its values are more variable and often higher (up to 571.84 µs), whereas s50000_aall is consistently the lowest and most stable.”
- **추출된 주장:** s50000_aall consistently lower than any s50000_aone run (85.033-571.84)
- **AI 라벨:** `wrong` — 근거: ranges overlap: 85.033 < 183.217
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 47 · DeepSeek-V3.2 · full

- **모델 문장:** “For s50000_aall, the retrieval P95 values range from 82.488 µs to 183.217 µs across 10 runs, consistently lower than any retrieval values for s1000000_aall (748.404 µs to 1023.152 µs), s1000000_aone (817.997 µs to 1419.669 µs), and s50000_aone (85.033 µs to 571.84 µs).”
- **추출된 주장:** s1000000 configurations range 748.404-1419.669 us
- **AI 라벨:** `correct` — 근거: minimum and maximum
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 48 · DeepSeek-V3.2 · full

- **모델 문장:** “Among all retrieval runs, s50000_aall consistently shows the lowest P95 latencies across multiple trials (e.g., 126.36 μs, 140.554 μs, 94.81 μs, 99.853 μs, 93.049 μs), with most values under 150 μs. … Therefore, s50000_aall is the clear choice for minimizing P95 latency based on the retrieval run evidence.”
- **추출된 주장:** lists all ten s50000_aall values
- **AI 라벨:** `correct` — 근거: runs 0-9
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 49 · DeepSeek-V3.2 · full

- **모델 문장:** “For s50000_aall, the P95 latencies across 10 runs are consistently low: 126.36, 140.554, 94.81, 99.853, 93.049, 183.217, 109.519, 82.488, 87.387, 87.347 µs. … The maximum among these is 183.217 µs, which is lower than the lowest P95 observed for any other config (e.g., s50000_aone has runs up to 571.84 µs, and s1000000 configs are all above 748 µs).”
- **추출된 주장:** maximum 183.217 is lower than the lowest P95 of any other config
- **AI 라벨:** `wrong` — 근거: s50000_aone minimum is 85.033
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 51 · DeepSeek-V3.2 · full

- **모델 문장:** “Among all retrieval runs, s50000_aall consistently shows the lowest P95 latencies across multiple trials (e.g., 126.36 μs, 140.554 μs, 94.81 μs, 99.853 μs, 93.049 μs), with most values under 150 μs. … Therefore, s50000_aall is the clear choice for minimizing P95 latency based on the retrieval run evidence.”
- **추출된 주장:** s50000_aall runs 126.36, 140.554, 94.81, 99.853, 93.049
- **AI 라벨:** `correct` — 근거: runs 0-4
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 53 · DeepSeek-V3.2 · full

- **모델 문장:** “In contrast, s50000_aone shows higher variability and often higher latencies (e.g., 571.84 μs, 272.927 μs), while both s1000000 configurations are consistently above 800 μs.”
- **추출된 주장:** ranges for all four configurations
- **AI 라벨:** `correct` — 근거: all minima and maxima match
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 54 · DeepSeek-V3.2 · full

- **모델 문장:** “For s50000_aall, the retrieval P95 values range from 82.488 µs to 183.217 µs across 10 runs, consistently lower than any retrieval values for s1000000_aall (748.404 µs to 1023.152 µs), s1000000_aone (817.997 µs to 1419.669 µs), and s50000_aone (85.033 µs to 571.84 µs). … While s50000_aone occasionally has low retrieval values (e.g., 85.033 µs), its values are more variable and often higher (up to 571.84 µs), whereas s50000_aall is consistently the lowest and most stable.”
- **추출된 주장:** s50000_aall consistently lower than any s50000_aone value
- **AI 라벨:** `wrong` — 근거: ranges overlap: 85.033 < 183.217
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 55 · Nemotron-3-Ultra-550B · full

- **모델 문장:** “Its P95 values range from 93.049 to 183.217 microseconds, which are significantly lower than the other configurations. … For comparison, s50000_aone ranges from 85.033 to 430.654 microseconds, s1000000_aall from 748.404 to 1023.152 microseconds, and s1000000_aone from 817.997”
- **추출된 주장:** cited s50000_aall runs range 93.049-183.217
- **AI 라벨:** `correct` — 근거: runs 0-5
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 58 · Nemotron-3-Ultra-550B · full

- **모델 문장:** “Among the allowed configurations, s50000_aall consistently shows the lowest P95 latency across all retrieval runs (runs 0-5). … For comparison, s50000_aone ranges from 85.033 to 430.654 microseconds, s1000000_aall from 748.404 to 1023.152 microseconds, and s1000000_aone from 817.997”
- **추출된 주장:** s50000_aall is lowest across all retrieval runs
- **AI 라벨:** `overstated` — 근거: lowest in 8 of 10 retrieval blocks
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 63 · Nemotron-3-Ultra-550B · full

- **모델 문장:** “Among the allowed configurations, s50000_aall consistently shows the lowest P95 latency across all retrieval runs (runs 0-5). … For comparison, s50000_aone ranges from 85.033 to 430.654 microseconds, s1000000_aall from 748.404 to 1023.152 microseconds, and s1000000_aone from 817.997”
- **추출된 주장:** s50000_aall is lowest across all retrieval runs
- **AI 라벨:** `overstated` — 근거: lowest in 8 of 10 retrieval blocks
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 69 · Nemotron-3-Ultra-550B · full

- **모델 문장:** “Among the allowed configurations, s50000_aall consistently shows the lowest P95 latency across all retrieval runs (runs 0-5). … For comparison, s50000_aone ranges from 85.033 to 430.654 microseconds, s1000000_aall from 748.404 to 1023.152 microseconds, and s1000000_aone from 817.997”
- **추출된 주장:** s50000_aall is lowest across all retrieval runs
- **AI 라벨:** `overstated` — 근거: lowest in 8 of 10 retrieval blocks
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 72 · Nemotron-3-Ultra-550B · full

- **모델 문장:** “Among the allowed configurations, s50000_aall consistently shows the lowest periodic wake-up P95 latency across all retrieval runs. … The P95 values for s50000_aall range from 82.488 to 183.217 microseconds, while s50000_aone ranges from 85.033 to 430.654 microseconds, and the s1000000 configurations show significantly higher latencies (748.404 to 1419.669 microseconds).”
- **추출된 주장:** s1000000 configurations range 748.404-1419.669
- **AI 라벨:** `correct` — 근거: minimum and maximum
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 73 · Nemotron-3-Ultra-550B · full

- **모델 문장:** “Among the allowed configurations, s50000_aall consistently shows the lowest P95 latency across all retrieval runs (runs 0-5). … For comparison, s50000_aone ranges from 85.033 to 430.654 microseconds, s1000000_aall from 748.404 to 1023.152 microseconds, and s1000000_aone from 817.997”
- **추출된 주장:** s50000_aall is lowest across all retrieval runs
- **AI 라벨:** `overstated` — 근거: lowest in 8 of 10 retrieval blocks
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 77 · Nemotron-3-Ultra-550B · full

- **모델 문장:** “Among the allowed configurations, s50000_aall consistently shows the lowest P95 latency across all retrieval runs (runs 0-5). … For comparison, s50000_aone ranges from 85.033 to 430.654 microseconds, s1000000_aall from 748.404 to 1023.152 microseconds, and s1000000_aone from 817.997”
- **추출된 주장:** s50000_aall is lowest across all retrieval runs
- **AI 라벨:** `overstated` — 근거: lowest in 8 of 10 retrieval blocks
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 78 · DeepSeek-V3.2 · full

- **모델 문장:** “Among all retrieval runs, s50000_aall consistently shows the lowest P95 latencies across multiple trials (e.g., 126.36 μs, 140.554 μs, 94.81 μs, 99.853 μs, 93.049 μs), with most values under 150 μs. … Therefore, s50000_aall is the clear choice for minimizing P95 latency based on the retrieval run evidence.”
- **추출된 주장:** s50000_aall is consistently the lowest in retrieval runs
- **AI 라벨:** `overstated` — 근거: lowest in 8 of 10 retrieval blocks
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 79 · DeepSeek-V3.2 · full

- **모델 문장:** “Among all retrieval runs, s50000_aall consistently shows the lowest P95 latencies across multiple trials (e.g., 126.36 μs, 140.554 μs, 94.81 μs, 99.853 μs, 93.049 μs), with most values under 150 μs. … Therefore, s50000_aall is the clear choice for minimizing P95 latency based on the retrieval run evidence.”
- **추출된 주장:** s50000_aall is consistently the lowest in retrieval runs
- **AI 라벨:** `overstated` — 근거: lowest in 8 of 10 retrieval blocks
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 81 · Gemini-3.8-Flash · full

- **모델 문장:** “In training-table, s50000_aall demonstrated the lowest overall mean P95 latency (132.94 us compared to 277.46 us for s50000_aone and >950 us for s1000000 configurations). … This is further confirmed across retrieval runs where s50000_aall consistently yielded low latencies, such as 126.36 us in retrieval-3-0, 93.05 us in retrieval-3-4, and 82.49 us in retrieval-3-7.”
- **추출된 주장:** s50000_aall reaches as low as 82.49 us
- **AI 라벨:** `correct` — 근거: minimum retrieval run
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 82 · Gemini-3.8-Flash · full

- **모델 문장:** “In training-table, s50000_aall demonstrated the lowest overall mean P95 latency (132.94 us compared to 277.46 us for s50000_aone and >950 us for s1000000 configurations). … This is further confirmed across retrieval runs where s50000_aall consistently yielded low latencies, such as 126.36 us in retrieval-3-0, 93.05 us in retrieval-3-4, and 82.49 us in retrieval-3-7.”
- **추출된 주장:** s50000_aall is consistently the lowest in retrieval runs
- **AI 라벨:** `overstated` — 근거: lowest in 8 of 10 retrieval blocks
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 84 · Gemini-3.8-Flash · full

- **모델 문장:** “In training-table, s50000_aall demonstrated the lowest overall mean P95 latency (132.94 us compared to 277.46 us for s50000_aone and >950 us for s1000000 configurations). … This is further confirmed across retrieval runs where s50000_aall consistently yielded low latencies, such as 126.36 us in retrieval-3-0, 93.05 us in retrieval-3-4, and 82.49 us in retrieval-3-7.”
- **추출된 주장:** s50000_aall reaches as low as 82.49 us
- **AI 라벨:** `correct` — 근거: minimum retrieval run
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 86 · Gemini-3.8-Flash · full

- **모델 문장:** “In training-table, s50000_aall demonstrated the lowest overall mean P95 latency (132.94 us compared to 277.46 us for s50000_aone and >950 us for s1000000 configurations). … This is further confirmed across retrieval runs where s50000_aall consistently yielded low latencies, such as 126.36 us in retrieval-3-0, 93.05 us in retrieval-3-4, and 82.49 us in retrieval-3-7.”
- **추출된 주장:** retrieval runs 0, 4, 7 give 126.36, 93.05, 82.49 us
- **AI 라벨:** `correct` — 근거: matches the runs
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 88 · Gemini-3.8-Flash · full

- **모델 문장:** “In training-table, s50000_aall demonstrated the lowest overall mean P95 latency (132.94 us compared to 277.46 us for s50000_aone and >950 us for s1000000 configurations). … This is further confirmed across retrieval runs where s50000_aall consistently yielded low latencies, such as 126.36 us in retrieval-3-0, 93.05 us in retrieval-3-4, and 82.49 us in retrieval-3-7.”
- **추출된 주장:** s50000_aall reaches as low as 82.49 us
- **AI 라벨:** `correct` — 근거: minimum retrieval run
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 89 · Gemini-3.8-Flash · full

- **모델 문장:** “In training-table, s50000_aall demonstrated the lowest overall mean P95 latency (132.94 us compared to 277.46 us for s50000_aone and >950 us for s1000000 configurations). … This is further confirmed across retrieval runs where s50000_aall consistently yielded low latencies, such as 126.36 us in retrieval-3-0, 93.05 us in retrieval-3-4, and 82.49 us in retrieval-3-7.”
- **추출된 주장:** s50000_aall is consistently the lowest in retrieval runs
- **AI 라벨:** `overstated` — 근거: lowest in 8 of 10 retrieval blocks
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 91 · Gemini-3.8-Flash · full

- **모델 문장:** “In training-table, s50000_aall demonstrated the lowest overall mean P95 latency (132.94 us compared to 277.46 us for s50000_aone and >950 us for s1000000 configurations). … This is further confirmed across retrieval runs where s50000_aall consistently yielded low latencies, such as 126.36 us in retrieval-3-0, 93.05 us in retrieval-3-4, and 82.49 us in retrieval-3-7.”
- **추출된 주장:** s50000_aall reaches as low as 82.49 us
- **AI 라벨:** `correct` — 근거: minimum retrieval run
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 93 · Gemini-3.1-Pro · full

- **모델 문장:** “The training table and retrieval runs demonstrate that the s50000_aall configuration minimizes periodic wake-up P95 latency. … Individual retrieval runs consistently confirm s50000_aall as the lowest latency option.”
- **추출된 주장:** s50000_aall is consistently the lowest in retrieval runs
- **AI 라벨:** `overstated` — 근거: lowest in 8 of 10 retrieval blocks
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

### id 96 · Gemini-3.1-Pro · full

- **모델 문장:** “The training table and retrieval runs demonstrate that the s50000_aall configuration minimizes periodic wake-up P95 latency. … Individual retrieval runs consistently confirm s50000_aall as the lowest latency option.”
- **추출된 주장:** s50000_aall is consistently the lowest in retrieval runs
- **AI 라벨:** `overstated` — 근거: lowest in 8 of 10 retrieval blocks
- **판단:** ☐ 맞음  ☐ 틀림 → 올바른 라벨: ______

