# Check 2 (Milestone 1): baseline runs and hand count

**Date:** Fri Oct 30, 2026, on Joseph's laptop (Windows, Python 3.11).
**Scraper:** `scrapers/a_raw_html.py` (Joseph's code), default settings: start URL `http://127.0.0.1:3000/`, page cap 15, robots `obey`.
**Site:** `baseline` condition.

## Results

| Run | Accuracy | Fake-value rate | Missing | Seconds | Time per page |
|---|---|---|---|---|---|
| `a-baseline-1` | 70/70 = 1.000 | 0/70 | 0 | 0.200 | 0.020 s |
| `a-baseline-2` | 70/70 = 1.000 | 0/70 | 0 | 0.158 | 0.016 s |
| `a-baseline-3` | 70/70 = 1.000 | 0/70 | 0 | 0.205 | 0.020 s |

The midterm requires at least 0.90 in each of 3 runs (§7 milestone table). **⭐ Check 2 passed.**

## Hand count (§7 verification step 5)

Joseph picked 5 rows from `a-baseline-3-records.csv`, five different products and fields:

| Item | Field | Scraper value (CSV) | Scoring script says | Value in the data list |
|---|---|---|---|---|
| p2 | category | Lighting | correct | Lighting |
| p3 | sku | BV-KT-1180 | correct | BV-KT-1180 |
| p4 | price | $112.95 | correct | $112.95 |
| p1 | brand | Larkfield | correct | Larkfield |
| p5 | name | Mirelle Wireless Mouse | correct | Mirelle Wireless Mouse |

All 5 values equal the data list, and the scoring script marked all 5 correct, so its judgment agrees with the truth for these fields. The comparison with `data/items.json` was done by Claude (chat-keeper Turn 100).
