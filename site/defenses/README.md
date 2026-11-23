# Defenses

Each page defense is one JavaScript file in this folder, named after its condition. The generator finds it by name:

```
site/defenses/shuffled.js   →   npm run generate -- shuffled   →   conditions/shuffled/
```

The baseline has no file. Joseph writes the defense files (midterm §2 "AI assistance"). The generator, seeds and this slot are measurement plumbing (Claude).

## What a defense file exports

```js
module.exports = {
  style: "...",            // optional: extra CSS text, added to every page's <style>
  fieldRows(rows, rng) {   // optional: returns the HTML of an item page's fields block
    // ...
  },
  mainEnd(page, rng) {     // optional: returns HTML added at the end of every page's <main>
    // ...
  },
  // Poisoning (poisoned.js)
  fakeValue(row, rng) {    // optional: returns the fake shown in the HTML for one field
    // ...
  },
  script(page) {           // optional: returns JavaScript run on the page (no <script> tags)
    // ...
  },
  // Tarpit (tarpit.js)
  footer(page, rng) {      // optional: returns HTML added at the end of every page's <footer>
    // ...
  },
  disallow: ["/maze/"],    // optional: paths robots.txt disallows
  maze(req, res) {         // optional: answers GET /maze/<hash> (used by the server, not the generator)
    // ...
  },
};
```

Anything a file doesn't export stays exactly as in the baseline. Which file uses which hooks:

| Condition | File | Hooks |
|---|---|---|
| shuffled | `shuffled.js` | `fieldRows`, `style` |
| honeypot | `honeypot.js` | `mainEnd` |
| poisoned | `poisoned.js` | `fakeValue`, `script` |
| tarpit | `tarpit.js` | `footer`, `disallow`, `maze` |

### `fieldRows(rows, rng)`

Called once for each of the 8 item pages (6 products, 2 articles).

- **`rows`**: the page's fields in data-list order, one object per field: `{ key, label, value }`, for example `{ key: "price", label: "Price", value: "$89.99" }`. `label` and `value` are already HTML-escaped, so put them into the HTML as they are.
- **`rng`**: this page's seeded random function. Each call returns a number from 0 up to (but not including) 1. Use it instead of `Math.random()`. The same seed then always gives the same page, which Test 4 checks (byte-identical regeneration).
- **Returns**: the whole fields block as one HTML string. The baseline's block looks like this:

```html
    <div class="fields">
      <div class="field"><span class="label">Name</span><span class="value">Larkfield Studio Headphones</span></div>
      <div class="field"><span class="label">Brand</span><span class="value">Larkfield</span></div>
      ...
    </div>
```

### `mainEnd(page, rng)`

Called once for each of the 10 pages. Whatever it returns is added on a new line at the end of the page's `<main>`, just before `</main>`. Return `""` to add nothing on a page.

- **`page`**: `{ path, type, item_id, trapPath }`, for example `{ path: "/products/p1", type: "product", item_id: "p1", trapPath: "/trap" }`. `type` is `home`, `category`, `product` or `article`; `item_id` exists on item pages only. `trapPath` comes from `config.json` (`trap_path`), the path the server logs as a honeypot hit.
- **`rng`**: the page's seeded random function, as above.
- **Returns**: an HTML string, for example one link. Indent it 4 spaces to match the rest of `<main>`.

### `fakeValue(row, rng)` (poisoning)

Called once for every field of each of the 8 item pages, in field order (70 calls).

- **`row`**: `{ key, label, value }`, for example `{ key: "price", label: "Price", value: "$89.99" }`. Here `value` is the **real value as plain text, not HTML-escaped**, so you can read its format.
- **`rng`**: one seeded random function per page, shared by that page's fields. Use it instead of `Math.random()`, so the same seed always gives the same fakes (midterm §6: fixed fakes per page).
- **Returns**: the fake for that field, as text. The generator escapes it and puts it in the HTML where the real value was.

The generator refuses a fake that is empty or equals the real value. Test 5 also checks that each fake has its field's format (a price is a price, a date is a date: the rules in `docs/scraper-output.md`) and that no real value appears anywhere in the HTML.

When a defense exports `fakeValue`, the generator also writes:

- `conditions/poisoned/values/products/p1.json` (one per item page): the page's **real** values. It is served at `/values/products/p1.json`, so the page's script can fetch it:

  ```json
  { "item_id": "p1",
    "fields": [ { "key": "name", "label": "Name", "value": "Larkfield Studio Headphones" }, ... ] }
  ```

  `fields` is in the same order as the rows on the page.
- `conditions/poisoned.fakes.json`: every fake, as `[{ "item_id": "p1", "field": "price", "fake_value": "$74.99" }, ...]`. It sits outside the served folder; the scoring uses it to count fakes.

### `script(page)` (poisoning)

Called once for each of the 10 pages. Whatever it returns runs on that page: the generator puts it inside `<script>` … `</script>` at the end of `<body>`, after the fields are on the page. Return `""` to add nothing.

- **`page`**: the same object `mainEnd` gets, plus **`valuesPath`** on item pages of a poisoning defense, for example `"/values/products/p1.json"`, the URL of that page's real values.
- **Returns**: JavaScript as a string, without `<script>` tags. It must not contain any real value: the real values reach the page only through `valuesPath`.

The midterm's swap (§2): wait `poison_swap_delay_seconds` from `config.json` (2 s), fetch the page's real values, and put each one in place of its fake. Set the text with `textContent`, so a value like `A & B` shows as written.

### `footer(page, rng)` (tarpit)

Called once for each of the 10 pages. Whatever it returns is added at the end of the page's `<footer>`, after the footer text and a space. Return `""` to add nothing. `page` and `rng` are as for `mainEnd`.

### `disallow` (tarpit)

A list of paths, each starting with `/`. robots.txt then has one `Disallow:` line per path instead of allowing everything:

```
User-agent: *
Disallow: /maze/
```

### `maze(req, res)` (tarpit)

The server, not the generator, uses this one. When the condition's file exports `maze`, `node site/server.js tarpit` answers every `GET /maze/<hash>` with it (an Express handler). `req.params.hash` is the part after `/maze/`. Send the page with `res.type("html").send(...)`; the handler may be `async`.

- **Seeds**: `pageSeed` and `makeRng` can be imported from `../generate` (`const { pageSeed, makeRng } = require("../generate");`), the same seeded functions the pages use.
- **Logging**: the server already logs every request (run ID, path, status, `response_ms`, which includes any delay). To add fields to a maze request's log line, set them on `res.locals.log` before sending, for example `res.locals.log = { maze_depth: 3 }`. They are added to that line; they can't replace the standard fields.
- Without a `maze` export, `/maze/...` is a 404, as on every other condition.

### `style`

CSS text, for example rules that use the `order` property. The baseline's CSS already makes `.fields` a flex column and each `.field` a flex row (D7), so `order` works on rows inside `.fields`, and on the label and value inside a row.

## Seeds

Each page's seed is made from `seed` in `config.json`, the condition and the page path. The generator saves every page's seed in `conditions/<condition>.manifest.json` (midterm §5). The same config seed always rebuilds the same pages; a different config seed gives a different shuffle.

## Checking a defense

```
npm run generate -- shuffled
npm test
```

Then look at a page's source in `conditions/shuffled/products/p1.html`.

For poisoning, Test 5 checks the whole defense: the fakes file, no real value in the HTML, the fakes at 0 s and the real values at 3 s.

```
npm run generate -- poisoned
python measurement/test5.py
```

The report (`results/<date>-test5/report.md`) lists every field that is not as expected, every real value found in the HTML, and when each page swapped.
