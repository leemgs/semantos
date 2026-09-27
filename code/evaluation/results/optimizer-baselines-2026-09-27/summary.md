# Matched-budget BO/RL baselines (offline replay)

Each method evaluates B recorded 2 ms training runs (bootstrap) and recommends one configuration, scored by the paired held-out replay used for all other selectors.

| Method | B | Control chosen | Expected paired change 5/8 ms (%) | Mean evaluations of 1 ms configs |
|---|---|---|---|---|
| random | 4 | 61.9% | -55.2 / -68.5 | 2.00 |
| random | 8 | 73.6% | -38.3 / -47.5 | 3.98 |
| random | 16 | 85.1% | -21.6 / -26.8 | 7.97 |
| random | 40 | 98.1% | -2.8 / -3.4 | 19.80 |
| egreedy | 4 | 64.9% | -50.9 / -63.1 | 2.00 |
| egreedy | 8 | 86.5% | -19.6 / -24.3 | 2.19 |
| egreedy | 16 | 94.6% | -7.8 / -9.7 | 2.58 |
| egreedy | 40 | 99.3% | -1.0 / -1.3 | 3.84 |
| ucb1 | 4 | 64.9% | -50.9 / -63.1 | 2.00 |
| ucb1 | 8 | 77.4% | -32.8 / -40.6 | 3.91 |
| ucb1 | 16 | 91.4% | -12.5 / -15.5 | 5.88 |
| ucb1 | 40 | 99.4% | -0.9 / -1.1 | 12.05 |
| gp_ei | 4 | 64.8% | -51.0 / -63.3 | 2.00 |
| gp_ei | 8 | 82.9% | -24.8 / -30.7 | 2.00 |
| gp_ei | 16 | 94.6% | -7.8 / -9.7 | 2.00 |
| gp_ei | 40 | 99.1% | -1.3 / -1.6 | 2.46 |
