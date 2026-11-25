# Results

57 runs from: `results/2026-11-18-experiment`, `results/2026-11-18-c-all`, `results/2026-11-20-d-all`, `results/2026-11-23-poisoned-2`, `results/2026-11-25-tarpit`.
Definitions: `scoring/results.py` and `docs/metrics-plan.md`.

| Scraper | Condition | Correct per run | Recall (min–max) | Precision | F1 | ESR | Reduction | Verdict | Honeypot detection | Time per page |
|---|---|---|---|---|---|---|---|---|---|---|
| (a) | baseline | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | — | baseline | 0.00 | 0.012 s |
| (a) | shuffled | 4 4 4 | 5.7% | 0.061 | 0.059 | 0.00 | 94.3% | stops | 0.00 | 0.016 s |
| (a) | honeypot | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | 0.0% | no effect | 1.00 | 0.017 s |
| (a) | poisoned | 0 0 0 | 0.0% | 0.000 | 0.000 | 0.00 | 100.0% | stops | 0.00 | 0.018 s |
| (a) | tarpit | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | 0.0% | no effect | 0.00 | 0.687 s |
| (b) | baseline | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | — | baseline | 0.00 | 0.023 s |
| (b) | shuffled | 4 4 4 | 5.7% | 0.061 | 0.059 | 0.00 | 94.3% | stops | 0.00 | 0.022 s |
| (b) | honeypot | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | 0.0% | no effect | 1.00 | 0.022 s |
| (b) | poisoned | 0 0 0 | 0.0% | 0.000 | 0.000 | 0.00 | 100.0% | stops | 0.00 | 0.025 s |
| (b) | tarpit | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | 0.0% | no effect | 0.00 | 0.723 s |
| (c) | baseline | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | — | baseline | 0.00 | 5.746 s |
| (c) | shuffled | 48 49 49 | 69.5% (68.6%–70.0%) | 0.807 | 0.747 | 0.00 | 30.5% | reduces | 0.00 | 5.451 s |
| (c) | honeypot | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | 0.0% | no effect | 1.00 | 5.356 s |
| (c) | poisoned | 0 0 0 | 0.0% | 0.000 | 0.000 | 0.00 | 100.0% | stops | 0.00 | 5.565 s |
| (d) | baseline | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | — | baseline | 0.00 | 3.035 s |
| (d) | shuffled | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | 0.0% | no effect | 0.00 | 3.037 s |
| (d) | honeypot | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | 0.0% | no effect | 0.00 | 3.036 s |
| (d) | poisoned | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | 0.0% | no effect | 0.00 | 4.652 s |
| (d) | tarpit | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | 0.0% | no effect | 0.00 | 3.728 s |

Poisoned site (a fake also counts as wrong): fakes and other wrong values per run.

| Scraper | Fakes per run | Fake-value rate | Other wrong per run | Missing per run |
|---|---|---|---|---|
| (a) | 70 70 70 | 100.0% | 0 0 0 | 0 0 0 |
| (b) | 70 70 70 | 100.0% | 0 0 0 | 0 0 0 |
| (c) | 70 70 70 | 100.0% | 0 0 0 | 0 0 0 |
| (d) | 0 0 0 | 0.0% | 0 0 0 | 0 0 0 |

Tarpit (§1 item 5): maze requests per run, from the request log.

| Scraper | Site | robots.txt | Maze pages per run | Seconds trapped per run | Server ms per maze request | Entered |
|---|---|---|---|---|---|---|
| (a) | tarpit | ignore | 5 5 5 | 10.1 10.1 10.1 | 2009 | 3 of 3 runs |
| (b) | tarpit | ignore | 5 5 5 | 10.3 10.2 10.2 | 2010 | 3 of 3 runs |
| (d) | tarpit | ignore | 5 5 5 | 22.2 22.3 22.2 | 2010 | 3 of 3 runs |

Failed runs (scored as finding nothing): none.
Runs whose request log shows a different page count from their output: none.
