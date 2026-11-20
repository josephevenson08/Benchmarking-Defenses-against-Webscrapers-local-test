# User cost, part 1

Run 2026-11-20T12:20:41 → 2026-11-20T12:22:27 · commit b3d1a05 · viewport 1280x800 · screenshots 3.0 s after load

| Condition | Pixel diff (mean / max) | SSIM (mean / min) | Reading-order mismatch | HTML size change |
|---|---|---|---|---|
| baseline | reference | reference | 0/70 fields = 0.000 | 21380 bytes (reference) |
| shuffled | 0.000% / 0.000% | 1.0000 / 1.0000 | 70/70 fields = 1.000 | +21.2% (max page +21.8%) |
| honeypot | 0.000% / 0.000% | 1.0000 / 1.0000 | 0/70 fields = 0.000 | +2.8% (max page +3.8%) |

Per page: `pages.csv`. Definitions: `measurement/user_cost.py`. Lighthouse and axe-core come in part 2.
