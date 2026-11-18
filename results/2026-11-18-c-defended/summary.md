# Experiment runs

Run 2026-11-18T12:22:10 → 2026-11-18T12:26:53 · commit 7d671e0 · scrapers c · conditions shuffled, honeypot · 3 runs per cell

| Run ID | Exit | Wall (s) | Accuracy | Pages | Time per page |
|---|---|---|---|---|---|
| `c-shuffled-1` | 0 | 64.424 | 47/70 = 0.671 | 10 | 6.301 s |
| `c-shuffled-2` | 0 | 48.041 | 50/70 = 0.714 | 10 | 4.692 s |
| `c-shuffled-3` | 0 | 46.411 | 50/70 = 0.714 | 10 | 4.534 s |
| `c-honeypot-1` | 1 | 43.536 | — | — | — |
| `c-honeypot-2` | 1 | 38.975 | — | — | — |
| `c-honeypot-3` | 1 | 38.897 | — | — | — |

**3 of 6 runs finished.** Failed: c-honeypot-1, c-honeypot-2, c-honeypot-3 (see `runs/<run-id>.log`).

Accuracy here is a quick check from `scoring/score.py`. The results CSV (with honeypot hits and time per page from the request log, and the standard metrics) is built from this folder in a separate step.
