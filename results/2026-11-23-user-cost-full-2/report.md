# User cost

Run 2026-11-23T13:48:52 → 2026-11-23T14:11:31 · commit f2414b1 · viewport 1280x800 · screenshots 3.0 s after load

## Visual, reading order and page weight

| Condition | Pixel diff (mean / max) | SSIM (mean / min) | Reading-order mismatch | HTML size change |
|---|---|---|---|---|
| baseline | reference | reference | 0/70 fields = 0.000 | 21380 bytes (reference) |
| shuffled | 0.000% / 0.000% | 1.0000 / 1.0000 | 70/70 fields = 1.000 | +21.2% (max page +21.8%) |
| honeypot | 0.000% / 0.000% | 1.0000 / 1.0000 | 0/70 fields = 0.000 | +2.8% (max page +3.8%) |
| poisoned | 0.000% / 0.000% | 1.0000 / 1.0000 | 0/70 fields = 0.000 | +17.5% (max page +25.0%) |

## Fakes on screen (poisoning)

Seconds from the start of the page load until the last field showed its real value.

| Condition | Pages that swapped | Mean | Max |
|---|---|---|---|
| poisoned | 8 | 2.02 s | 2.03 s |

## Accessibility (axe-core, all 10 pages)

| Condition | Violations | New vs baseline | Critical / serious / moderate / minor | WCAG A / AA / AAA / best practice |
|---|---|---|---|---|
| baseline | 0 | reference | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| shuffled | 0 | 0 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| honeypot | 0 | 0 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| poisoned | 0 | 0 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |

## Speed (Lighthouse 13.6.0, {'formFactor': 'mobile', 'throttlingMethod': 'simulate'}, median of 5 runs per page, mean over the 10 pages)

| Condition | Score | FCP | LCP | TTI |
|---|---|---|---|---|
| baseline | 100.0 | 607 ms | 607 ms | 662 ms |
| shuffled | 99.8 (-0.2) | 607 ms (+0 ms) | 607 ms (+0 ms) | 671 ms (+9 ms) |
| honeypot | 99.8 (-0.2) | 607 ms (+0 ms) | 607 ms (+0 ms) | 679 ms (+16 ms) |
| poisoned | 100.0 (+0.0) | 609 ms (+2 ms) | 609 ms (+2 ms) | 631 ms (-31 ms) |

Per page: `pages.csv`. Definitions: `measurement/user_cost.py`.
