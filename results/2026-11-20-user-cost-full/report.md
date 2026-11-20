# User cost

Run 2026-11-20T12:46:11 → 2026-11-20T13:03:31 · commit 7bc9d62 · viewport 1280x800 · screenshots 3.0 s after load

## Visual, reading order and page weight

| Condition | Pixel diff (mean / max) | SSIM (mean / min) | Reading-order mismatch | HTML size change |
|---|---|---|---|---|
| baseline | reference | reference | 0/70 fields = 0.000 | 21380 bytes (reference) |
| shuffled | 0.000% / 0.000% | 1.0000 / 1.0000 | 70/70 fields = 1.000 | +21.2% (max page +21.8%) |
| honeypot | 0.000% / 0.000% | 1.0000 / 1.0000 | 0/70 fields = 0.000 | +2.8% (max page +3.8%) |

## Accessibility (axe-core, all 10 pages)

| Condition | Violations | New vs baseline | Critical / serious / moderate / minor | WCAG A / AA / AAA / best practice |
|---|---|---|---|---|
| baseline | 0 | reference | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| shuffled | 0 | 0 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| honeypot | 0 | 0 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |

## Speed (Lighthouse 13.6.0, {'formFactor': 'mobile', 'throttlingMethod': 'simulate'}, median of 5 runs per page, mean over the 10 pages)

| Condition | Score | FCP | LCP | TTI |
|---|---|---|---|---|
| baseline | 100.0 | 607 ms | 607 ms | 648 ms |
| shuffled | 100.0 (+0.0) | 607 ms (-0 ms) | 607 ms (-0 ms) | 669 ms (+22 ms) |
| honeypot | 100.0 (+0.0) | 607 ms (+0 ms) | 607 ms (+0 ms) | 641 ms (-7 ms) |

Per page: `pages.csv`. Definitions: `measurement/user_cost.py`.
