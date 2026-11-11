# Test 3: the extraction rule

Run 2026-11-11T11:55:29 · commit c0972ff

| Case | Scraper | Expected records | Got | Missing | Extra | Wrong value | |
|---|---|---|---|---|---|---|---|
| `baseline-p2` | (a) | 10 | 10 | — | — | — | PASS |
| `baseline-p2` | (b) | 10 | 10 | — | — | — | PASS |
| `shuffled-p1` | (a) | 9 | 9 | — | — | — | PASS |
| `shuffled-p1` | (b) | 9 | 9 | — | — | — | PASS |

**Test 3 ((a) and (b)): PASS**

Each case's page is served on its own and each scraper runs with `--page-cap 1`. Scraper outputs are in `outputs/`. (d) and the poisoned page are added once they are built.
