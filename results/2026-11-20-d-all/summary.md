# Experiment runs

Run 2026-11-20T13:34:05 → 2026-11-20T13:38:50 · commit 2065190 · scrapers d · conditions baseline, shuffled, honeypot · 3 runs per cell

| Run ID | Exit | Wall (s) | Accuracy | Pages | Time per page |
|---|---|---|---|---|---|
| `d-baseline-1` | 0 | 31.808 | 70/70 = 1.000 | 10 | 3.038 s |
| `d-baseline-2` | 0 | 31.412 | 70/70 = 1.000 | 10 | 3.035 s |
| `d-baseline-3` | 0 | 31.358 | 70/70 = 1.000 | 10 | 3.032 s |
| `d-shuffled-1` | 0 | 31.388 | 70/70 = 1.000 | 10 | 3.037 s |
| `d-shuffled-2` | 0 | 31.329 | 70/70 = 1.000 | 10 | 3.038 s |
| `d-shuffled-3` | 0 | 31.199 | 70/70 = 1.000 | 10 | 3.036 s |
| `d-honeypot-1` | 0 | 31.193 | 70/70 = 1.000 | 10 | 3.035 s |
| `d-honeypot-2` | 0 | 31.171 | 70/70 = 1.000 | 10 | 3.035 s |
| `d-honeypot-3` | 0 | 31.262 | 70/70 = 1.000 | 10 | 3.038 s |

**9 of 9 runs finished.**

Accuracy here is a quick check from `scoring/score.py`. The results CSV (with honeypot hits and time per page from the request log, and the standard metrics) is built from this folder in a separate step.
