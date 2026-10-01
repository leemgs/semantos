# Claim-label review: explanations and evidence

Use with `claim-label-review.csv`. For each audited explanation below, check that (1) every quantitative or comparative claim in it appears as a row in the CSV, and (2) each row's drafted label is right given the evidence facts. Leave `reviewer_label` empty to accept a label; otherwise enter one of: correct, overstated, wrong, partly wrong, wrong unit, wrong attribution, unsupported prior. Add a row note if a claim is missing.

## Evidence facts (all latencies in microseconds)

- Training means (P95): s50000_aall 132.94, s50000_aone 277.46, s1000000_aall 954.76, s1000000_aone 1080.66
- Retrieval runs (P95, evidence order, blocks 0-9):
  - s50000_aall: 126.36, 140.554, 94.81, 99.853, 93.049, 183.217, 109.519, 82.488, 87.387, 87.347
  - s50000_aone: 571.84, 272.927, 151.299, 254.509, 170.306, 430.654, 97.457, 89.789, 85.033, 150.643
- Retrieval mean / min / max: s50000_aall 110.5 / 82.488 / 183.217; s50000_aone 227.4 / 85.033 / 571.84; s1000000_aall 953.1 / 748.404 / 1023.152; s1000000_aone 1014.0 / 817.997 / 1419.669
- Lowest per retrieval block: s50000_aall in 8 of 10 blocks, s50000_aone in 2.

## Qwen2.5-7B (local, all variants): CSV rows 0, 1, 2, 3, 4

**full**, seed 4088, chose `s50000_aall`:

> Based on the training summaries and retrieval runs provided, the configuration 's50000_aall' has the lowest P95 latency for periodic wake-ups. The training table shows that 's50000_aall' has a significantly lower average P95 latency (126.36 microseconds) compared to other configurations. Additionally, the retrieval runs consistently show that 's50000_aall' has the lowest P95 latency across various

**no_graph**, seed 4088, chose `s50000_aall`:

> The configuration 's50000_aall' has the lowest P95 latency among the provided evidence, with a value of 93.049 microseconds. This configuration also shows consistent low P95 latency across multiple retrieval runs, indicating its effectiveness in minimizing periodic wake-up P95 latency.

**no_retrieval**, seed 4088, chose `s50000_aall`:

> Based on the training summaries provided in the 'training-table', the configuration 's50000_aall' has the lowest periodic wake-up P95 latency at 132.9413. Therefore, to minimize the periodic wake-up P95 latency, the 's50000_aall' configuration is the optimal choice among the given options.

**model_only**, seed 4088, chose `s50000_aone`:

> To minimize periodic wake-up P95 latency, we should choose a configuration that balances the frequency of wake-ups and the latency of responses. The 's50000_aone' configuration has a moderate wake-up interval and a single active core, which can help in reducing the latency compared to the 's1000000_aone' configuration, which has a much longer wake-up interval. The 's50000_aall' and 's1000000_aall'

## Llama-3.1-8B (local, all variants): CSV rows 5, 6, 7, 8, 9, 10, 11

**full**, seed 4088, chose `s50000_aone`:

> The config 's50000_aone' has the lowest P95 latency of 571.84 us among all the allowed configs. This is because it has the lowest P95 latency in 6 out of the 9 retrieval runs, indicating that it is the most efficient config for minimizing periodic wake-up latency.

**no_graph**, seed 4088, chose `s50000_aone`:

> The config 's50000_aone' has the lowest average P95 latency across all retrieval runs, with an average of 272.927 us. This suggests that this config is the best choice for minimizing periodic wake-up P95 latency.

**no_retrieval**, seed 4088, chose `s50000_aone`:

> Based on the provided evidence, the configuration 's50000_aone' has the lowest measured training summary value of 277.4647, indicating the lowest periodic wake-up P95 latency.

**model_only**, seed 4088, chose `s50000_aone`:

> Based on the provided allowed configs, 's50000_aone' is chosen to minimize periodic wake-up P95 latency. This is because the 'one' in 'aone' suggests a more aggressive approach, which can lead to faster wake-up times. However, without specific evidence, this is a general assumption.

**delete_cited**, seed 4088, chose `s1000000_aall`:

> The config 's1000000_aall' has the lowest P95 latency of 748.404 us among all the allowed configs.

**delete_uncited**, seed 4088, chose `s50000_aall`:

> The config 's50000_aall' has the lowest P95 latency of 82.488 us among all the allowed configs. This is evident from the retrieval runs 'retrieval-3-2-s50000_aall', 'retrieval-3-4-s50000_aall', 'retrieval-3-6-s50000_aall', 'retrieval-3-7-s50000_aall', and 'retrieval-3-8-s50000_aall' which all show a P95 latency of less than 100 us. The training summary 'training-table' also shows that 's50000_aall

## Qwen2.5-14B (local, all variants): CSV rows 12, 13, 14, 15, 16, 17

**full**, seed 4088, chose `s50000_aall`:

> Based on the provided evidence, the configuration 's50000_aall' has the lowest P95 latency across all retrieval runs. The training summary shows that 's50000_aall' has a P95 latency of 132.9413 ms, which is significantly lower than the other configurations. The retrieval runs also consistently show lower P95 latencies for 's50000_aall' compared to the other configurations.

**no_graph**, seed 4088, chose `s50000_aall`:

> The configuration 's50000_aall' has the lowest P95 latency among the allowed configurations. According to the training summary table, 's50000_aall' has a P95 latency of 132.9413 ms. Additionally, the retrieval runs show that 's50000_aall' consistently has the lowest P95 latency across multiple runs, with the highest being 183.217 ms and the lowest being 82.488 ms.

**no_retrieval**, seed 4088, chose `s50000_aall`:

> Based on the provided evidence, the configuration 's50000_aall' has the lowest periodic wake-up P95 latency of 132.9413 milliseconds. This is significantly lower than the other configurations, making it the optimal choice for minimizing latency.

**model_only**, seed 4088, chose `s50000_aone`:

> Based on the provided evidence, there is no direct measurement or comparison available between the allowed configurations. However, the configuration 's50000_aone' suggests a smaller dataset size (50,000) with a more focused approach (aone), which could potentially reduce the periodic wake-up P95 latency compared to larger dataset sizes or more generalized approaches. This is a heuristic choice, a

## Phi-4 (local, all variants): CSV rows 18, 19, 20, 21, 22, 23, 24, 25, 26, 27

**full**, seed 4088, chose `s50000_aall`:

> The configuration 's50000_aall' consistently shows the lowest P95 latency across multiple retrieval runs. The P95 latencies for 's50000_aall' are 126.36, 140.554, 94.81, 99.853, 93.049, and 183.217 microseconds, which are significantly lower than those of the other configurations. This indicates that 's50000_aall' minimizes periodic wake-up P95 latency effectively.

**no_graph**, seed 4088, chose `s50000_aall`:

> The configuration 's50000_aall' consistently shows the lowest P95 latency across multiple retrieval runs. The P95 latencies for 's50000_aall' are 126.36, 140.554, 94.81, 99.853, 93.049, and 183.217 microseconds, which are significantly lower than those of the other configurations. This indicates that 's50000_aall' minimizes periodic wake-up P95 latency effectively.

**no_retrieval**, seed 4088, chose `s50000_aall`:

> The goal is to minimize the periodic wake-up P95 latency. From the 'training-table' evidence, the P95 latencies for the configurations are as follows: 's50000_aall' has a latency of 132.9413, 's50000_aone' has 277.4647, 's1000000_aall' has 954.7558, and 's1000000_aone' has 1080.6555. Among these, 's50000_aall' has the lowest P95 latency of 132.9413, making it the optimal choice for minimizing the 

**model_only**, seed 4088, chose `s1000000_aone`:

> Given the absence of specific evidence in the provided data, the decision is based on general principles of system performance optimization. The configuration 's1000000_aone' suggests a larger sample size (1,000,000) with a single active component ('aone'), which typically reduces the frequency of wake-ups compared to configurations with multiple active components. This reduction in wake-up events

**delete_cited**, seed 4088, chose `s50000_aone`:

> The configuration 's50000_aone' consistently shows the lowest P95 latency across multiple retrieval runs. The P95 latencies for 's50000_aone' are 571.84, 272.927, 151.299, 254.509, 170.306, and 430.654 microseconds, which are significantly lower than those of the other configurations. This indicates that 's50000_aone' minimizes periodic wake-up P95 latency effectively.

**delete_uncited**, seed 4088, chose `s50000_aall`:

> The configuration 's50000_aall' consistently shows the lowest P95 latency across multiple retrieval runs. The P95 latencies for 's50000_aall' are 126.36, 140.554, 94.81, 99.853, 93.049, and 183.217 microseconds, which are significantly lower than those of the other configurations. This indicates that 's50000_aall' minimizes the periodic wake-up P95 latency effectively.

## Llama-3.3-70B (hosted, full context): CSV rows 28, 29, 30, 31, 32, 33, 34

**full**, seed 4088, chose `s50000_aall`:

> The config 's50000_aall' has the lowest average p95 latency across multiple retrieval runs, with values ranging from 82.488 to 183.217 us. This suggests that 's50000_aall' is the most consistent and efficient config in terms of minimizing periodic wake-up P95 latency.

**full**, seed 4089, chose `s50000_aall`:

> The config 's50000_aall' has the lowest P95 latency values across multiple retrieval runs, with values ranging from 82.488 to 140.554. This suggests that 's50000_aall' is the most effective config for minimizing periodic wake-up P95 latency.

**full**, seed 4090, chose `s50000_aall`:

> The config 's50000_aall' has the lowest average p95 latency across multiple retrieval runs (e.g., 'retrieval-3-2-s50000_aall', 'retrieval-3-3-s50000_aall', 'retrieval-3-4-s50000_aall', 'retrieval-3-7-s50000_aall', 'retrieval-3-8-s50000_aall', 'retrieval-3-9-s50000_aall') with values ranging from 82.488 to 126.36, indicating a more consistent and lower periodic wake-up P95 latency compared to other

**full**, seed 4092, chose `s50000_aall`:

> The config 's50000_aall' has the lowest average p95 latency across multiple retrieval runs (94.81, 82.488, 87.387, 87.347) compared to other configs.

Note: Qwen3-235B returned three distinct full-context responses, two of which share the same explanation text.

## Qwen3-235B (hosted, full context): CSV rows 35, 36, 37, 38, 39, 40

**full**, seed 4088, chose `s50000_aall`:

> The goal is to minimize P95 latency during periodic wake-up. Among all configurations, 's50000_aall' consistently shows the lowest P95 latency across multiple retrieval runs (e.g., 126.36 us, 140.554 us, 94.81 us, etc.), with the highest observed P95 being 183.217 us. In contrast, all other configurations (including 's50000_aone', 's1000000_aall', and 's1000000_aone') exhibit significantly higherP

**full**, seed 4092, chose `s50000_aall`:

> The goal is to minimize P95 latency during periodic wake-up. Among all configurations, 's50000_aall' consistently shows the lowest P95 latency across multiple retrieval runs (e.g., 126.36 us, 140.554 us, 94.81 us, etc.), with the highest observed P95 being 183.217 us. In contrast, all other configurations, including 's50000_aone', 's1000000_aall', and 's1000000_aone', exhibit significantly higherP

## DeepSeek-V3.2 (hosted, full context): CSV rows 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 78, 79

**full**, seed 4088, chose `s50000_aall`:

> The goal is to minimize periodic wake-up P95 latency. The evidence includes a training summary table showing average latencies, but the primary evidence for periodic wake-up latency should come from the retrieval runs, which are measured at a fixed period_ns of 3,000,000 ns (3 ms). Among all retrieval runs, s50000_aall consistently shows the lowest P95 latencies across multiple trials (e.g., 126.36 μs, 140.554 μs, 94.81 μs, 99.853 μs, 93.049 μs), with most values under 150 μs. In contrast, s50000_aone shows higher variability and often higher latencies (e.g., 571.84 μs, 272.927 μs), while both s1000000 configurations are consistently above 800 μs. Therefore, s50000_aall is the clear choice for minimizing P95 latency based on the retrieval run evidence.

**full**, seed 4089, chose `s50000_aall`:

> The goal is to minimize periodic wake-up P95 latency. The evidence includes a training summary table showing average latencies, where s50000_aall has the lowest average (132.9413 µs). More importantly, the retrieval runs provide direct P95 latency measurements for each config at a 3 ms period. For s50000_aall, the P95 latencies across 10 runs are consistently low: 126.36, 140.554, 94.81, 99.853, 93.049, 183.217, 109.519, 82.488, 87.387, 87.347 µs. The maximum among these is 183.217 µs, which is lower than the lowest P95 observed for any other config (e.g., s50000_aone has runs up to 571.84 µs, and s1000000 configs are all above 748 µs). Therefore, s50000_aall has the lowest worst-case P95 latency based on the measured retrieval runs, making it the best choice to minimize periodic wake-up P95 latency.

**full**, seed 4090, chose `s50000_aall`:

> The goal is to minimize periodic wake-up P95 latency. The evidence includes a training table showing average latencies, and multiple retrieval runs with measured p95_us latencies for each config at a 3,000,000 ns period. The training table indicates s50000_aall has the lowest average latency (132.9413 µs). The retrieval runs consistently show s50000_aall has the lowest p95 latencies across multiple trials (e.g., 126.36 µs, 140.554 µs, 94.81 µs, 99.853 µs, 93.049 µs), with most under 150 µs, while other configs (especially s1000000_aall and s1000000_aone) typically exceed 800 µs. Therefore, s50000_aall is selected as it minimizes the periodic wake-up P95 latency based on the provided evidence.

**full**, seed 4091, chose `s50000_aall`:

> The goal is to minimize periodic wake-up P95 latency. The evidence provides two types of data: training summaries (table) and retrieval runs. The training table shows a single P95 latency value per config, with s50000_aall having the lowest (132.9413 µs). The retrieval runs provide multiple P95 measurements per config at a 3 ms period. For s50000_aall, the retrieval P95 values range from 82.488 µs to 183.217 µs across 10 runs, consistently lower than any retrieval values for s1000000_aall (748.404 µs to 1023.152 µs), s1000000_aone (817.997 µs to 1419.669 µs), and s50000_aone (85.033 µs to 571.84 µs). While s50000_aone occasionally has low retrieval values (e.g., 85.033 µs), its values are more variable and often higher (up to 571.84 µs), whereas s50000_aall is consistently the lowest and most stable. Therefore, s50000_aall minimizes the periodic wake-up P95 latency based on the available evidence.

**full**, seed 4092, chose `s50000_aall`:

> The goal is to minimize periodic wake-up P95 latency. The evidence includes a training summary table showing average latencies, where s50000_aall has the lowest (132.9413 µs). More importantly, the retrieval runs provide direct P95 latency measurements for each config at a 3 ms period. For s50000_aall, the ten retrieval runs show P95 latencies ranging from 82.488 µs to 183.217 µs, consistently lower than any run for s50000_aone (85.033 µs to 571.84 µs) and far lower than the s1000000 configs (748.404 µs to 1419.669 µs). The lowest observed P95 latencies across all runs are from s50000_aall (e.g., 82.488 µs in retrieval-3-7-s50000_aall), making it the best choice to minimize latency.

## Nemotron-3-Ultra-550B (hosted, full context): CSV rows 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77

**full**, seed 4088, chose `s50000_aall`:

> Among the allowed configurations, s50000_aall consistently shows the lowest P95 latency across all retrieval runs (runs 0-5). Its P95 values range from 93.049 to 183.217 microseconds, which are significantly lower than the other configurations. For comparison, s50000_aone ranges from 85.033 to 430.654 microseconds, s1000000_aall from 748.404 to 1023.152 microseconds, and s1000000_aone from 817.997

**full**, seed 4089, chose `s50000_aall`:

> Among the allowed configurations, s50000_aall consistently achieves the lowest periodic wake-up P95 latency across all retrieval runs. Its P95 values range from 82.5 to 183.2 microseconds, with most runs below 150 microseconds. In contrast, s50000_aone shows higher variability (85.0 to 430.7 microseconds), while both s1000000_aall and s1000000_aone consistently exceed 748 microseconds. The s50000_

**full**, seed 4090, chose `s50000_aall`:

> Among the allowed configurations, s50000_aall consistently shows the lowest P95 latency across multiple retrieval runs (runs 0-5 shown). Its P95 values range from ~82-183 μs, while s50000_aone ranges from ~85-431 μs, s1000000_aall from ~748-1023 μs, and s1000000_aone from ~817-1420 μs. The training-table evidence (id: training-table) also confirms s50000_aall has the lowest measured value (132.94)

**full**, seed 4091, chose `s50000_aall`:

> Among the allowed configurations, s50000_aall consistently shows the lowest periodic wake-up P95 latency across all retrieval runs. The P95 values for s50000_aall range from 82.488 to 183.217 microseconds, while s50000_aone ranges from 85.033 to 430.654 microseconds, and the s1000000 configurations show significantly higher latencies (748.404 to 1419.669 microseconds). The training table also s500

**full**, seed 4092, chose `s50000_aall`:

> Among the allowed configurations, s50000_aall consistently shows the lowest P95 latency across all retrieval runs. The P95 values for s50000_aall range from 82.488 to 183.217 microseconds, while s50000_aone ranges from 85.033 to 430.654 microseconds, and the s1000000 configurations are all above 748 microseconds. The training table (training-table) also confirms s50000_aall has the lowest measured

## Gemini-3.8-Flash (hosted, full context): CSV rows 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91

**full**, seed 4088, chose `s50000_aall`:

> In training-table, s50000_aall demonstrated the lowest overall mean P95 latency (132.94 us compared to 277.46 us for s50000_aone and >950 us for s1000000 configurations). This is further confirmed across retrieval runs where s50000_aall consistently yielded low latencies, such as 126.36 us in retrieval-3-0, 93.05 us in retrieval-3-4, and 82.49 us in retrieval-3-7.

**full**, seed 4089, chose `s50000_aall`:

> According to training-table, s50000_aall yields the lowest baseline latency at 132.9413 us compared to 277.4647 us for s50000_aone and ~954-1080 us for the 1000000-scale configurations. Across retrieval runs, s50000_aall consistently maintains the lowest P95 wake-up latency, dropping as low as 82.488 us.

**full**, seed 4090, chose `s50000_aall`:

> Config s50000_aall consistently delivers the lowest P95 wake-up latency, averaging 132.94 us in the training table and reaching down to 82.49 us in individual retrieval runs, outperforming all other configurations.

**full**, seed 4091, chose `s50000_aall`:

> In training-table, s50000_aall achieves the lowest P95 latency at 132.9413 us compared to 277.4647 us for s50000_aone and over 950 us for the s1000000 variants. Retrieval runs consistently confirm this, with s50000_aall measuring as low as 82.488 us in retrieval-3-7-s50000_aall.

**full**, seed 4092, chose `s50000_aall`:

> In training-table, s50000_aall achieves the lowest overall P95 latency (132.94 us vs 277.46 us for s50000_aone and >950 us for s1000000 variants). This performance is corroborated across retrieval runs where s50000_aall consistently achieves low latencies, dropping as low as 82.49 us.

## Gemini-3.1-Pro (hosted, full context): CSV rows 92, 93, 94, 95, 96

**full**, seed 4088, chose `s50000_aall`:

> The training table and retrieval runs demonstrate that the s50000_aall configuration minimizes periodic wake-up P95 latency. The training summary shows s50000_aall achieves a P95 latency of 132.94 us, significantly lower than s50000_aone (277.46 us) and the 1,000,000 configurations (>950 us). Individual retrieval runs consistently confirm s50000_aall as the lowest latency option.

**full**, seed 4090, chose `s50000_aall`:

> The configuration s50000_aall minimizes the periodic wake-up P95 latency. The training table shows it has the lowest average P95 latency at 132.94 us, outperforming all other configurations. This is corroborated by multiple retrieval runs where s50000_aall consistently achieves the lowest P95 latency, frequently dropping below 100 us.

