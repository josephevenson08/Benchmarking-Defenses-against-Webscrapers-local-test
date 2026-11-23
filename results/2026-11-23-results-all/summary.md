# Results

48 runs from: `results/2026-11-18-experiment`, `results/2026-11-18-c-all`, `results/2026-11-20-d-all`, `results/2026-11-23-poisoned-2`.
Definitions: `scoring/results.py` and `docs/metrics-plan.md`.

| Scraper | Condition | Correct per run | Recall (min–max) | Precision | F1 | ESR | Reduction | Verdict | Honeypot detection | Time per page |
|---|---|---|---|---|---|---|---|---|---|---|
| (a) | baseline | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | — | baseline | 0.00 | 0.012 s |
| (a) | shuffled | 4 4 4 | 5.7% | 0.061 | 0.059 | 0.00 | 94.3% | stops | 0.00 | 0.016 s |
| (a) | honeypot | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | 0.0% | no effect | 1.00 | 0.017 s |
| (a) | poisoned | 0 0 0 | 0.0% | 0.000 | 0.000 | 0.00 | 100.0% | stops | 0.00 | 0.018 s |
| (b) | baseline | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | — | baseline | 0.00 | 0.023 s |
| (b) | shuffled | 4 4 4 | 5.7% | 0.061 | 0.059 | 0.00 | 94.3% | stops | 0.00 | 0.022 s |
| (b) | honeypot | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | 0.0% | no effect | 1.00 | 0.022 s |
| (b) | poisoned | 0 0 0 | 0.0% | 0.000 | 0.000 | 0.00 | 100.0% | stops | 0.00 | 0.025 s |
| (c) | baseline | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | — | baseline | 0.00 | 5.746 s |
| (c) | shuffled | 48 49 49 | 69.5% (68.6%–70.0%) | 0.807 | 0.747 | 0.00 | 30.5% | reduces | 0.00 | 5.451 s |
| (c) | honeypot | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | 0.0% | no effect | 1.00 | 5.356 s |
| (c) | poisoned | 0 0 0 | 0.0% | 0.000 | 0.000 | 0.00 | 100.0% | stops | 0.00 | 5.565 s |
| (d) | baseline | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | — | baseline | 0.00 | 3.035 s |
| (d) | shuffled | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | 0.0% | no effect | 0.00 | 3.037 s |
| (d) | honeypot | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | 0.0% | no effect | 0.00 | 3.036 s |
| (d) | poisoned | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | 0.0% | no effect | 0.00 | 4.652 s |

Poisoned site (a fake also counts as wrong): fakes and other wrong values per run.

| Scraper | Fakes per run | Fake-value rate | Other wrong per run | Missing per run |
|---|---|---|---|---|
| (a) | 70 70 70 | 100.0% | 0 0 0 | 0 0 0 |
| (b) | 70 70 70 | 100.0% | 0 0 0 | 0 0 0 |
| (c) | 70 70 70 | 100.0% | 0 0 0 | 0 0 0 |
| (d) | 0 0 0 | 0.0% | 0 0 0 | 0 0 0 |

Failed runs (scored as finding nothing): none.
Runs whose request log shows a different page count from their output: none.
