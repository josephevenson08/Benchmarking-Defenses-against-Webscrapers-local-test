# Test 3 cases

Each folder is one Test 3 case (midterm §5, Test 3). `measurement/test3.py` serves its `page.html` on its own at the case's path and runs scrapers (a) and (b) on it with `--page-cap 1`, then compares what they extracted with `expected.json`.

| Case | Page | Saved from |
|---|---|---|
| `baseline-p2/` | `/products/p2` | `conditions/baseline/` on Nov 10 |
| `shuffled-p1/` | `/products/p1` | `conditions/shuffled/` on Nov 10 (config seed 20261021, `site/defenses/shuffled.js` at `eef2fdf`) |

`page.html` is a saved copy, so a case never changes under the test, even if the generator or a defense changes later.

## `expected.json` (worked out by hand: Joseph)

Work it out from `page.html` by hand, as the midterm asks. Don't run a scraper to fill it in, because then the test would only check the scraper against itself.

```json
{
  "path": "/products/p2",
  "records": [
    {"field": "<key from data/fields.json>", "value": "<text the rule would take>"}
  ]
}
```

For each of the 15 labels in `data/fields.json`, do what the label-then-next-element rule does:

1. Find the element whose whole text is exactly the label (for example `Price`). If no element has that text, there is no record for that field.
2. Take the element that comes right after that label's element in the HTML source (its next sibling). If there is none (the label's element is the last one in its block), there is no record.
3. The value is that element's text, exactly as written between its tags (`&amp;` counts as `&`). The field is the label's key from `data/fields.json`: `name`, `brand`, `category`, `price`, `sku`, `rating`, `review_count`, `availability`, `release_date`, `description` (products) or `title`, `author`, `publish_date`, `tags`, `summary` (articles).

Order doesn't matter. Then run `python measurement/test3.py`.
