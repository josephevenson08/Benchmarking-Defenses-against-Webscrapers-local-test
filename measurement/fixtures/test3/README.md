# Test 3 cases

Each folder is one Test 3 case (midterm §5, Test 3). `measurement/test3.py` serves its `page.html` on its own at the case's path and runs scrapers (a), (b) and (d) on it with `--page-cap 1`, then compares what each extracted with its expected file.

| Case | Page | Saved from |
|---|---|---|
| `baseline-p2/` | `/products/p2` | `conditions/baseline/` on Nov 10 |
| `shuffled-p1/` | `/products/p1` | `conditions/shuffled/` on Nov 10 (config seed 20261021, `site/defenses/shuffled.js` at `eef2fdf`) |
| `poisoned-p1/` | `/products/p1` | `conditions/poisoned/` on Nov 27 (config seed 20261021, `site/defenses/poisoned.js` at `910ee22`); its real values are in `serve/values/products/p1.json`, served at `/values/products/p1.json` so the page's swap works |

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

## `expected-d.json`: what scraper (d) should get (also by hand: Joseph)

(d) uses the same rule, with two differences, so on some pages its answer differs from (a) and (b)'s:

1. **It reads the page as it looks on screen.** It sorts the label and value elements by their CSS `order` (the `style="order: N"` on each element in a shuffled page), smallest first. Then "the next element" means the next one in that on-screen order, not in the HTML source.
2. **It reads the page after it stops changing.** On the poisoned page that's after the swap, so it gets the **real** values from `serve/values/products/p1.json`, not the fakes in the HTML.

| Case | `expected.json` ((a) and (b)) | `expected-d.json` ((d)) |
|---|---|---|
| `baseline-p2` | done | not needed: on a normal page (d) gets the same as (a) and (b), so it uses `expected.json` |
| `shuffled-p1` | done | **to fill in:** label then next element, in `order` number order |
| `poisoned-p1` | **to fill in:** the values written in `page.html` (the fakes) | **to fill in:** the real values from `serve/values/products/p1.json` |

The three files to fill in are there with `"records": []`. Until they're filled in, Test 3 reports those cases as FAIL ("no records yet").
