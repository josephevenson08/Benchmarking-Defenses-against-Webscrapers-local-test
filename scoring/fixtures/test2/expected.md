# Test 2: expected result

Written by hand by Joseph before the scoring script existed (midterm §5 Test 2, §7 verification step 1).
Files: `output.json` (pretend scraper output, 69 records) and `fakes.json` (2 fake values).

## The 7 special fields

| Page | Field | Value in output.json | Real value | Counts as |
|---|---|---|---|---|
| /products/p1 | category | (no record) | Headphones | missing |
| /products/p1 | price | $89O.99 | $89.99 | malformed |
| /products/p1 | review_count | 1,289 | 1,284 |  plain wrong |
| /products/p2 | sku | "" (empty) | CV-LT-0317 | missing |
| /products/p3 | price | $41.00 | $47.00 | fake |
| /articles/a1 | publish_date | 2025-05-19 | 2025-05-14 | fake |
| /articles/a2 | publish_date | null | 2025-08-02 | missing |

All other fields in output.json match the real values.

## Calculation

- Total scored fields: 70
- Missing: 3
- Wrong: 4 (fakes: 2, malformed: 1, plain wrong: 1)
- Correct = 70 − 3 − 4 = 63
- **Accuracy** = 63 / 70 = 0.90
- **Fake-value rate** = 2 / 70 = 0.029