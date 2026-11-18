# Experiment runs

Run 2026-11-18T12:32:52 → 2026-11-18T12:41:38 · commit 8e361f3 · scrapers c · conditions baseline, shuffled, honeypot · 3 runs per cell

| Run ID | Exit | Wall (s) | Accuracy | Pages | Time per page |
|---|---|---|---|---|---|
| `c-baseline-1` | 0 | 69.934 | 70/70 = 1.000 | 10 | 6.878 s |
| `c-baseline-2` | 0 | 52.407 | 70/70 = 1.000 | 10 | 5.133 s |
| `c-baseline-3` | 0 | 53.338 | 70/70 = 1.000 | 10 | 5.227 s |
| `c-shuffled-1` | 0 | 65.35 | 48/70 = 0.686 | 10 | 6.417 s |
| `c-shuffled-2` | 0 | 49.224 | 49/70 = 0.700 | 10 | 4.813 s |
| `c-shuffled-3` | 0 | 52.284 | 49/70 = 0.700 | 10 | 5.122 s |
| `c-honeypot-1` | 0 | 62.29 | 70/70 = 1.000 | 11 | 5.559 s |
| `c-honeypot-2` | 0 | 55.553 | 70/70 = 1.000 | 11 | 4.951 s |
| `c-honeypot-3` | 0 | 62.192 | 70/70 = 1.000 | 11 | 5.557 s |

**9 of 9 runs finished.**

Accuracy here is a quick check from `scoring/score.py`. The results CSV (with honeypot hits and time per page from the request log, and the standard metrics) is built from this folder in a separate step.
