# Test 4: shuffled keeps the layout

Run 2026-11-10T11:26:18 · commit 991bfcc · config seed 20261021

| Check | Result | |
|---|---|---|
| 1. Same seed gives byte-identical files | 12 files compared, 0 differ | PASS |
| 2. Source order differs from baseline on every item page | 8 of 8 item pages differ | PASS |
| 3. Pixel difference at most 1.0% | max 0.000%, mean 0.000% over 10 pages | PASS |
| 4. 10 screenshot pairs checked by eye | see `by-eye.md` (Joseph) | — |

**Automated part: PASS**

## Source order per item page

| Page | Elements | Order differs | Label still directly followed by its value |
|---|---|---|---|
| `/products/p1` | 20 | yes | 0 of 10 |
| `/products/p2` | 20 | yes | 0 of 10 |
| `/products/p3` | 20 | yes | 1 of 10 |
| `/products/p4` | 20 | yes | 0 of 10 |
| `/products/p5` | 20 | yes | 1 of 10 |
| `/products/p6` | 20 | yes | 0 of 10 |
| `/articles/a1` | 10 | yes | 0 of 5 |
| `/articles/a2` | 10 | yes | 2 of 5 |

## Pixel difference per page

| Page | Different pixels |
|---|---|
| `articles-a1.png` | 0.000% |
| `articles-a2.png` | 0.000% |
| `index.png` | 0.000% |
| `products-p1.png` | 0.000% |
| `products-p2.png` | 0.000% |
| `products-p3.png` | 0.000% |
| `products-p4.png` | 0.000% |
| `products-p5.png` | 0.000% |
| `products-p6.png` | 0.000% |
| `products.png` | 0.000% |

Screenshots: `screenshots/` (1280×800 viewport, full page, 3.0 s wait). Difference images: `screenshots/diff/`.
