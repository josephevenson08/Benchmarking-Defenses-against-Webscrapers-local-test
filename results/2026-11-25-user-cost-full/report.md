# User cost

Run 2026-11-25T10:48:09 → 2026-11-25T11:23:06 · commit fb007e2 · viewport 1280x800 · screenshots 3.0 s after load

## Visual, reading order and page weight

| Condition | Pixel diff (mean / max) | SSIM (mean / min) | Reading-order mismatch | HTML size change |
|---|---|---|---|---|
| baseline | reference | reference | 0/70 fields = 0.000 | 21380 bytes (reference) |
| shuffled | 0.000% / 0.000% | 1.0000 / 1.0000 | 70/70 fields = 1.000 | +21.2% (max page +21.8%) |
| honeypot | 0.000% / 0.000% | 1.0000 / 1.0000 | 0/70 fields = 0.000 | +2.8% (max page +3.8%) |
| poisoned | 0.000% / 0.000% | 1.0000 / 1.0000 | 0/70 fields = 0.000 | +17.5% (max page +25.0%) |
| tarpit | 0.015% / 0.015% | 0.9991 / 0.9991 | 0/70 fields = 0.000 | +1.6% (max page +2.2%) |

## Fakes on screen (poisoning)

Seconds from the start of the page load until the last field showed its real value.

| Condition | Pages that swapped | Mean | Max |
|---|---|---|---|
| poisoned | 8 | 2.04 s | 2.06 s |

## Accessibility (axe-core, all 10 pages)

| Condition | Violations | New vs baseline | Critical / serious / moderate / minor | WCAG A / AA / AAA / best practice |
|---|---|---|---|---|
| baseline | 0 | reference | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| shuffled | 0 | 0 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| honeypot | 0 | 0 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| poisoned | 0 | 0 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| tarpit | 0 | 0 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |

## Speed (Lighthouse 13.6.0, {'formFactor': 'mobile', 'throttlingMethod': 'simulate'}, median of 5 runs per page, mean over the 10 pages)

| Condition | Score | FCP | LCP | TTI |
|---|---|---|---|---|
| baseline | 99.4 | 611 ms | 611 ms | 760 ms |
| shuffled | 98.9 (-0.5) | 619 ms (+8 ms) | 619 ms (+8 ms) | 921 ms (+161 ms) |
| honeypot | 98.6 (-0.8) | 620 ms (+9 ms) | 620 ms (+9 ms) | 905 ms (+145 ms) |
| poisoned | 99.1 (-0.3) | 622 ms (+10 ms) | 622 ms (+10 ms) | 916 ms (+156 ms) |
| tarpit | 98.7 (-0.7) | 620 ms (+9 ms) | 620 ms (+9 ms) | 953 ms (+194 ms) |

Per page: `pages.csv`. Definitions: `measurement/user_cost.py`.
