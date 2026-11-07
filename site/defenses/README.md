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
};
```

Anything a file doesn't export stays exactly as in the baseline. More hooks, such as one for the honeypot link and one for the poisoning script, are added when those defenses start.

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
