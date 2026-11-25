# Scrapers against defenses

Three measures (D118): accuracy, detection rate and cost to visitors. Made by `measurement/compare.py` from `cells.csv` (scoring/results.py) and `cost.csv` (measurement/user_cost.py).

## 1. Accuracy: share of the 70 fields each scraper got right

| Scraper | baseline | shuffled | honeypot | poisoned | tarpit |
|---|---|---|---|---|---|
| (a) raw HTML | 100% | 5.7% (stops) | 100% (no effect) | 0% (stops) | 100% (no effect) |
| (b) browser | 100% | 5.7% (stops) | 100% (no effect) | 0% (stops) | 100% (no effect) |
| (c) LLM | 100% | 69.5% (reduces) | 100% (no effect) | 0% (stops) | — |
| (d) adaptive | 100% | 100% (no effect) | 100% (no effect) | 100% (no effect) | 100% (no effect) |

- **Shuffling** stops (a), (b); reduces (c); has no effect on (d).
- **Poisoning** stops (a), (b), (c); has no effect on (d).

## 2. Detection rate: share of each scraper's runs the trap caught

| Scraper | honeypot | tarpit |
|---|---|---|
| (a) raw HTML | 100% (3 of 3 runs) | 100% (3 of 3 runs) |
| (b) browser | 100% (3 of 3 runs) | 100% (3 of 3 runs) |
| (c) LLM | 100% (3 of 3 runs) | — |
| (d) adaptive | 0% (0 of 3 runs) | 100% (3 of 3 runs) |

- **Honeypot** catches (a), (b), (c) in every run; never catches (d). Its accuracy is unchanged, so this is how it shows.
- **Tarpit** catches (a), (b), (d) in every run. Its accuracy is unchanged, so this is how it shows. Only scrapers set to ignore robots.txt walk in; ones that obey it never enter (Test 6).

Time the tarpit wasted (scrapers set to ignore robots.txt):

| Scraper | Maze pages per run | Seconds trapped per run | Server time per maze page |
|---|---|---|---|
| (a) raw HTML | 5.0 | 10.1 s | 2.0 s |
| (b) browser | 5.0 | 10.2 s | 2.0 s |
| (d) adaptive | 5.0 | 22.2 s | 2.0 s |

## 3. Cost to visitors

| Defense | Load-time change (LCP) | Fields out of reading order | Fake values on screen |
|---|---|---|---|
| Shuffling | +8 ms | 70 of 70 | none |
| Honeypot | +9 ms | 0 of 70 | none |
| Poisoning | +10 ms | 0 of 70 | 2.06 s |
| Tarpit | +9 ms | 0 of 70 | none |

Load-time changes this small are within the baseline's own run-to-run noise. Also checked, with no change for any defense: how the page looks after loading (SSIM 1.000) and accessibility violations (axe-core: 0).
