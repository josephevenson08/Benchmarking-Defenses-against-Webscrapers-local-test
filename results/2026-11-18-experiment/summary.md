# Experiment runs

Run 2026-11-18T11:11:06 → 2026-11-18T11:11:27 · commit defff7a · scrapers a, b · conditions baseline, shuffled, honeypot · 3 runs per cell

| Run ID | Exit | Wall (s) | Accuracy | Pages | Time per page |
|---|---|---|---|---|---|
| `a-baseline-1` | 0 | 0.613 | 70/70 = 1.000 | 10 | 0.014 s |
| `a-baseline-2` | 0 | 0.451 | 70/70 = 1.000 | 10 | 0.009 s |
| `a-baseline-3` | 0 | 0.472 | 70/70 = 1.000 | 10 | 0.013 s |
| `b-baseline-1` | 0 | 1.758 | 70/70 = 1.000 | 10 | 0.023 s |
| `b-baseline-2` | 0 | 1.297 | 70/70 = 1.000 | 10 | 0.022 s |
| `b-baseline-3` | 0 | 1.256 | 70/70 = 1.000 | 10 | 0.024 s |
| `a-shuffled-1` | 0 | 0.487 | 4/70 = 0.057 | 10 | 0.015 s |
| `a-shuffled-2` | 0 | 0.501 | 4/70 = 0.057 | 10 | 0.015 s |
| `a-shuffled-3` | 0 | 0.529 | 4/70 = 0.057 | 10 | 0.018 s |
| `b-shuffled-1` | 0 | 1.463 | 4/70 = 0.057 | 10 | 0.024 s |
| `b-shuffled-2` | 0 | 1.276 | 4/70 = 0.057 | 10 | 0.022 s |
| `b-shuffled-3` | 0 | 1.152 | 4/70 = 0.057 | 10 | 0.020 s |
| `a-honeypot-1` | 0 | 0.512 | 70/70 = 1.000 | 11 | 0.017 s |
| `a-honeypot-2` | 0 | 0.465 | 70/70 = 1.000 | 11 | 0.016 s |
| `a-honeypot-3` | 0 | 0.579 | 70/70 = 1.000 | 11 | 0.019 s |
| `b-honeypot-1` | 0 | 1.206 | 70/70 = 1.000 | 11 | 0.023 s |
| `b-honeypot-2` | 0 | 1.274 | 70/70 = 1.000 | 11 | 0.023 s |
| `b-honeypot-3` | 0 | 1.339 | 70/70 = 1.000 | 11 | 0.021 s |

**18 of 18 runs finished.**

Accuracy here is a quick check from `scoring/score.py`. The results CSV (with honeypot hits and time per page from the request log, and the standard metrics) is built from this folder in a separate step.
