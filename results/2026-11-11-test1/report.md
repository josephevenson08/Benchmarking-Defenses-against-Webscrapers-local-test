# Test 1: normal workflow

Run 2026-11-11T12:05:12 · commit 7c5ae6c · baseline served on port 3100

## Conditions: 10 pages and 70 scored fields each

| Condition | HTML pages | Manifest pages | Manifest fields | Label elements | Value elements | |
|---|---|---|---|---|---|---|
| baseline | 10 | 10 | 70 | 70 | 70 | PASS |
| shuffled | 10 | 10 | 70 | 70 | 70 | PASS |
| honeypot | 10 | 10 | 70 | 70 | 70 | PASS |

## Runs on baseline: each at least 90% accurate

| Run | Accuracy | Fake-value rate | Missing | Pages | Seconds | Time per page | |
|---|---|---|---|---|---|---|---|
| `a-baseline-1` | 70/70 = 1.000 | 0/70 | 0 | 10 | 0.146 | 0.015 s | PASS |
| `a-baseline-2` | 70/70 = 1.000 | 0/70 | 0 | 10 | 0.163 | 0.016 s | PASS |
| `a-baseline-3` | 70/70 = 1.000 | 0/70 | 0 | 10 | 0.174 | 0.017 s | PASS |
| `b-baseline-1` | 70/70 = 1.000 | 0/70 | 0 | 10 | 0.306 | 0.031 s | PASS |
| `b-baseline-2` | 70/70 = 1.000 | 0/70 | 0 | 10 | 0.26 | 0.026 s | PASS |
| `b-baseline-3` | 70/70 = 1.000 | 0/70 | 0 | 10 | 0.268 | 0.027 s | PASS |

**Test 1: PASS**

Scraper outputs: `runs/`. Request log: `requests.jsonl`.
