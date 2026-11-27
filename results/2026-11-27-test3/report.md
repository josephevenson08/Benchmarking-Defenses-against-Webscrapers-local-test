# Test 3: the extraction rule

Run 2026-11-27T12:28:03 · commit 710fa59

| Case | Scraper | Expected file | Expected records | Got | Missing | Extra | Wrong value | |
|---|---|---|---|---|---|---|---|---|
| `baseline-p2` | (a) | `expected.json` | 10 | 10 | — | — | — | PASS |
| `baseline-p2` | (b) | `expected.json` | 10 | 10 | — | — | — | PASS |
| `baseline-p2` | (d) | `expected.json` | 10 | 10 | — | — | — | PASS |
| `poisoned-p1` | (a) | `expected.json` | 10 | 10 | — | — | — | PASS |
| `poisoned-p1` | (b) | `expected.json` | 10 | 10 | — | — | — | PASS |
| `poisoned-p1` | (d) | `expected-d.json` | 10 | 10 | — | — | — | PASS |
| `shuffled-p1` | (a) | `expected.json` | 9 | 9 | — | — | — | PASS |
| `shuffled-p1` | (b) | `expected.json` | 9 | 9 | — | — | — | PASS |
| `shuffled-p1` | (d) | `expected-d.json` | 10 | 10 | — | — | — | PASS |

**Test 3 ((a), (b), (d)): PASS**

Each case's page is served on its own and each scraper runs with `--page-cap 1`. Scraper outputs are in `outputs/`.
