# Scraper output format and matching rules

**Status:** approved by Joseph on Oct 26 (chat-keeper Turn 9; decisions D31–D35). Amended Oct 30 with Joseph's approval (D47): the default start URL is now `http://127.0.0.1:3000/`. That covers the output format, the inputs, ignoring case in text fields, and conflicting duplicates counting as wrong. Changes after this point must be recorded in the chat-keeper.

This is the contract between the scrapers and the scoring script. Every scraper, (a) through (e), writes one JSON file per run in the format below. The scoring script reads that file and decides, for each of the 70 scored fields, whether the scraper got it right.

It is based on:
- **§2 Baseline scrapers:** "Take a start URL, a page cap and a robots.txt setting. Output JSON records (page, field, value) plus crawl stats."
- **Figure 2:** the Run and ExtractedRecord entities.
- **§4 Metrics:** the accuracy and fake-value formulas.

---

## Inputs every scraper takes

The experiment runner (Milestone 3) starts each scraper with these command-line options:

| Option | Meaning | Default (`config.json`) |
|---|---|---|
| `--start-url` | Where the crawl starts | `http://127.0.0.1:3000/` (see the note below) |
| `--page-cap` | Stop after requesting this many pages | `15` |
| `--robots obey` or `--robots ignore` | Whether to follow `robots.txt` | `obey` |
| `--run-id` | The run ID, for example `a-baseline-1` | — (required) |
| `--out` | Where to write the output JSON | — (required) |

**The run ID** has the form `<scraper>-<condition>-<run number>`, for example `a-baseline-1`.
- The scraper treats it as plain text. It only puts it in its User-Agent (`run=<id>`) and in its output.
- The scoring script reads the condition and run number from it.
- Scrapers are never told the condition directly. §4 assumes "scrapers know nothing of the defenses beyond their built capabilities."

**Why `127.0.0.1`, not `localhost`:** on Joseph's Windows laptop, the name `localhost` added about 2 s to every request: 20.6 s for 10 pages, against 0.11 s with `127.0.0.1`. That would distort the time-per-page metric (§4). `127.0.0.1` is the same machine without the name lookup (D47).

**Labels:** scrapers read field labels from `data/fields.json`. They must never read `data/items.json`, which is the answer key.

---

## Output file

One UTF-8 JSON file per run. Trimmed example from scraper (a) on the baseline site:

```json
{
  "run": {
    "run_id": "a-baseline-1",
    "scraper": "a",
    "start_url": "http://127.0.0.1:3000/",
    "page_cap": 15,
    "obey_robots_txt": true,
    "started_at": "2026-10-28T19:02:11.481Z",
    "seconds": 0.84
  },
  "pages": [
    { "path": "/", "status": 200, "error": null },
    { "path": "/products/", "status": 200, "error": null },
    { "path": "/products/p1", "status": 200, "error": null }
  ],
  "records": [
    { "page": "/products/p1", "field": "name", "value": "Larkfield Studio Headphones" },
    { "page": "/products/p1", "field": "price", "value": "$89.99" }
  ]
}
```

### `run`: one per file (Figure 2's Run)

| Key | Type | Meaning |
|---|---|---|
| `run_id` | text | As passed in `--run-id` |
| `scraper` | text | `a`, `b`, `c`, `d` or `e` |
| `start_url`, `page_cap`, `obey_robots_txt` | as passed | The inputs, saved for the record |
| `started_at` | ISO 8601 time | When the crawl started |
| `seconds` | number | Crawl time, from just before the first request to after the last page is processed |

Figure 2's `pages_fetched` is not stored here; the scoring script counts the `pages` list. Figure 2's `condition` and `run_number` come from the run ID. Following the midterm, the scoring script calculates everything it can, so there is one source of truth.

### `pages`: every page URL the scraper requested

Every request goes in this list except `robots.txt`.

| Key | Type | Meaning |
|---|---|---|
| `path` | text | The path requested, for example `/products/p1` |
| `status` | number or `null` | HTTP status; `null` if no response arrived |
| `error` | text or `null` | `null` when the request worked. Otherwise a short code, for example `timeout`, `connection_error`, or for (c) and (e) `invalid_json`, `missing_key` or `model_timeout` |

This list covers the midterm's "Record 404s and timeouts and keep going" (§2) and lets Test 7 check failure handling. **Time per page** = `seconds` / number of entries in `pages` (§4).

### `records`: the fields found (Figure 2's ExtractedRecord)

| Key | Type | Meaning |
|---|---|---|
| `page` | text | The path of the page the value came from. A full URL is also accepted. |
| `field` | text | The field **key** from `data/fields.json`, for example `price` or `review_count`, not the label text |
| `value` | text, number or `null` | The value as extracted. Scraper (c) may give price and rating as numbers (§2). |

The scraper writes only what it found. A field it couldn't find simply has no record. The scoring script fills in all 70 rows (Figure 2 constraint: "A missing field is stored as empty and incorrect").

---

## Matching rules (how the scoring script decides "correct")

§4 Assumptions: "A value is correct if it matches the data list after normalizing." These are the normalization rules. §2 says Joseph specifies them.

| Field | Rule | Counted correct for `p1` |
|---|---|---|
| `price` | Remove `$` and `,`; read as a number; compare to 2 decimals. Not a number → **malformed → wrong**. | `$89.99`, `89.99`, `89.99` (number) |
| `rating` | Read as a number. Not a number → malformed → wrong. | `4.5`, `4.50` |
| `review_count` | Remove `,`; read as a whole number. Not a whole number → malformed → wrong. | `1,284`, `1284` |
| `release_date`, `publish_date` | Exact text after trimming spaces. | `2024-09-12` |
| `tags` | Split on commas and trim each tag; compare as a set, ignoring order and case (D26). | `kitchen, Cookware,cleaning` |
| Every other field | Trim, collapse repeated spaces, ignore case. | `larkfield studio  headphones` |

Other rules:
- **Missing:** no record, `null`, or empty text → missing → wrong.
- **Fake (poisoned site only):** the value matches that page's fake value under the same rules → counted as fake, and wrong.
- **Duplicates:** the same page and field reported more than once. Identical values count once. Conflicting values count as **wrong**, because the scraper didn't commit to one answer.
- **Ignored:** records for pages that aren't item pages, or for unknown field keys. They are neither right nor wrong.
- **Pages:** each page path is matched to its item through the condition's manifest (`conditions/<condition>.manifest.json`). A full URL, a trailing `/` or a `.html` ending still matches.

**Metrics (§4):**
- **Accuracy** = correct fields / 70.
- **Fake-value rate** = fake fields / 70.

---

## Fake-values file

Written by the poisoning defense in Milestone 3, and needed now for the Test 2 fixture. It is a list with one entry per poisoned field, matching Figure 2's FakeValue (unique per item and field, and never equal to the real value):

```json
[
  { "item_id": "p1", "field": "price", "fake_value": "$74.99" },
  { "item_id": "p1", "field": "sku", "fake_value": "LF-HP-2047" }
]
```

On conditions without poisoning there is no fake-values file, and the fake-value rate is 0.

---

## What this means for the Test 2 fixture

The fixture (§5 Test 2) is made of:
1. a scraper output file in this format, with 63 correct values, 4 wrong values and 3 missing fields, where:
   - 2 of the wrong values equal the page's fake value;
   - 1 wrong value is a malformed price, such as `$8a.99`;
   - the 4th wrong value is just wrong;
2. a small fake-values file that holds those 2 fakes.

Expected result: **accuracy 63/70 = 0.90** and **fake-value rate 2/70 ≈ 0.029**. The malformed value counts as wrong without stopping the scoring.
