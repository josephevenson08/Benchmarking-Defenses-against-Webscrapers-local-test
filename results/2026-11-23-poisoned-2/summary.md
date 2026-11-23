# Experiment runs

Run 2026-11-23T13:05:12 → 2026-11-23T13:10:33 · commit 910ee22 · scrapers a, b, c, d · conditions poisoned · 3 runs per cell

| Run ID | Exit | Wall (s) | Accuracy | Pages | Time per page |
|---|---|---|---|---|---|
| `a-poisoned-1` | 0 | 0.675 | 0/70 = 0.000 | 10 | 0.020 s |
| `a-poisoned-2` | 0 | 0.495 | 0/70 = 0.000 | 10 | 0.016 s |
| `a-poisoned-3` | 0 | 0.513 | 0/70 = 0.000 | 10 | 0.018 s |
| `b-poisoned-1` | 0 | 1.296 | 0/70 = 0.000 | 10 | 0.025 s |
| `b-poisoned-2` | 0 | 1.28 | 0/70 = 0.000 | 10 | 0.026 s |
| `b-poisoned-3` | 0 | 1.272 | 0/70 = 0.000 | 10 | 0.025 s |
| `c-poisoned-1` | 0 | 65.575 | 0/70 = 0.000 | 10 | 6.436 s |
| `c-poisoned-2` | 0 | 52.728 | 0/70 = 0.000 | 10 | 5.142 s |
| `c-poisoned-3` | 0 | 52.22 | 0/70 = 0.000 | 10 | 5.116 s |
| `d-poisoned-1` | 0 | 47.566 | 70/70 = 1.000 | 10 | 4.658 s |
| `d-poisoned-2` | 0 | 47.565 | 70/70 = 1.000 | 10 | 4.650 s |
| `d-poisoned-3` | 0 | 47.546 | 70/70 = 1.000 | 10 | 4.649 s |

**12 of 12 runs finished.**

Accuracy here is a quick check from `scoring/score.py`. The results CSV (with honeypot hits and time per page from the request log, and the standard metrics) is built from this folder in a separate step.
