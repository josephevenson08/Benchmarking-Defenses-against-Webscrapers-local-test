# Results tables

Made 2026-11-23 by `measurement/figures.py` from `cells.csv` (scoring/results.py) and `cost.csv` (measurement/user_cost.py).

## Table 1. Extraction quality by defense and scraper

| Scraper | Site | Correct per run | Recall (min–max) | Precision | F1 | ESR | Drop in recall | Verdict | Fake-value rate |
|---|---|---|---|---|---|---|---|---|---|
| (a) raw HTML | baseline | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | — | baseline | — |
| (a) raw HTML | shuffled | 4 4 4 | 5.7% | 0.061 | 0.059 | 0.00 | 94.3% | stops | — |
| (a) raw HTML | honeypot | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | 0.0% | no effect | — |
| (a) raw HTML | poisoned | 0 0 0 | 0.0% | 0.000 | 0.000 | 0.00 | 100.0% | stops | 100.0% |
| (b) browser | baseline | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | — | baseline | — |
| (b) browser | shuffled | 4 4 4 | 5.7% | 0.061 | 0.059 | 0.00 | 94.3% | stops | — |
| (b) browser | honeypot | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | 0.0% | no effect | — |
| (b) browser | poisoned | 0 0 0 | 0.0% | 0.000 | 0.000 | 0.00 | 100.0% | stops | 100.0% |
| (c) LLM | baseline | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | — | baseline | — |
| (c) LLM | shuffled | 48 49 49 | 69.5% (68.6%–70.0%) | 0.807 | 0.747 | 0.00 | 30.5% | reduces | — |
| (c) LLM | honeypot | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | 0.0% | no effect | — |
| (c) LLM | poisoned | 0 0 0 | 0.0% | 0.000 | 0.000 | 0.00 | 100.0% | stops | 100.0% |
| (d) adaptive | baseline | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | — | baseline | — |
| (d) adaptive | shuffled | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | 0.0% | no effect | — |
| (d) adaptive | honeypot | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | 0.0% | no effect | — |
| (d) adaptive | poisoned | 70 70 70 | 100.0% | 1.000 | 1.000 | 1.00 | 0.0% | no effect | 0.0% |

## Table 2. Honeypot and speed

| Scraper | Honeypot detection rate | Evasion rate | Trap hits (honeypot runs) | Time per page (baseline) | Slowdown vs (a) |
|---|---|---|---|---|---|
| (a) raw HTML | 1.00 | 0.00 | 3 | 0.012 s | 1× |
| (b) browser | 1.00 | 0.00 | 3 | 0.023 s | 2× |
| (c) LLM | 1.00 | 0.00 | 3 | 5.746 s | 479× |
| (d) adaptive | 0.00 | 1.00 | 0 | 3.035 s | 253× |

False-positive rate: planned (a human-like visitor that clicks only visible links, Sun Nov 29).

## Table 3. User cost against baseline

| Site | Pixel diff (max) | SSIM (min) | Fields out of reading order | HTML size | axe-core violations (new) | Lighthouse score | FCP | LCP | TTI | Fakes on screen (max) |
|---|---|---|---|---|---|---|---|---|---|---|
| shuffled | 0.000% | 1.0000 | 70/70 | +21.2% | 0 (0) | -0.2 | +0 ms | +0 ms | +9 ms | — |
| honeypot | 0.000% | 1.0000 | 0/70 | +2.8% | 0 (0) | -0.2 | +0 ms | +0 ms | +16 ms | — |
| poisoned | 0.000% | 1.0000 | 0/70 | +17.5% | 0 (0) | +0.0 | +2 ms | +2 ms | -31 ms | 2.03 s |

Lighthouse changes are the mean over the 10 pages of each page's median of 5 runs; a change smaller than the baseline's own run-to-run range is not counted as an effect (§5).

## Table 4. Our results next to published ones (same metric)

| Metric | Ours | Published | Source | Main difference |
|---|---|---|---|---|
| Drop in scraping recall caused by the defense | shuffling: 94.3% (a), 94.3% (b), 30.5% (c), 0.0% (d); poisoning: 100.0% (a), 100.0% (b), 100.0% (c), 0.0% (d) | 100% (88.7% → 0%) | WebCloak, IEEE S&P 2026 | Real pages and frontier-model agents; they protect mainly images |
| Speed cost of the defense (Lighthouse) | no change beyond noise | LCP +0.88 s; score −0.3 to −5.5 | WebCloak | Their defense adds scripts; ours adds CSS or one link |
| Extraction success rate on simple HTML (baseline) | 1.00 (a), 1.00 (b), 1.00 (c), 1.00 (d) | 0.82–1.00 | Beyond BeautifulSoup, AAAI 2026 | Whole tasks on real sites vs 70 scored fields |
| Bot detection rate | honeypot: 1.00 (a), 1.00 (b), 1.00 (c), 0.00 (d) | 67.6% of bots at 3.0% false positives | Shy Guys, 2026 | Passive classification of real traffic vs a link trap |
| Evasion by an adaptive bot | (d) evades the honeypot in every run | 44.6–52.9% evasion of commercial detectors | FP-Inconsistent, 2025 | Paid evasive bot services vs our own scraper |
