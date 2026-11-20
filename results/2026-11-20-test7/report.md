# Test 7: failure handling (crawl part)

Run 2026-11-20T13:10:42 · commit 86db946 · slow page answers after 12 s

| Scraper | Page cap | Pages visited (path status error) | Checks | |
|---|---|---|---|---|
| (a) | 15 | `/ 200`<br>`/t7/a 200`<br>`/t7/missing 404`<br>`/t7/slow None timeout`<br>`/t7/b 200` | ✅ finished without crashing<br>✅ every page visited<br>✅ no page visited twice (no loop)<br>✅ 404 recorded<br>✅ timeout recorded<br>✅ kept going after the timeout<br>✅ other pages loaded | PASS |
| (a) | 3 | `/ 200`<br>`/t7/a 200`<br>`/t7/missing 404` | ✅ finished without crashing<br>✅ stopped at the page cap (3)<br>✅ started at /<br>✅ no page visited twice | PASS |
| (b) | 15 | `/ 200`<br>`/t7/a 200`<br>`/t7/missing 404`<br>`/t7/slow None timeout`<br>`/t7/b 200` | ✅ finished without crashing<br>✅ every page visited<br>✅ no page visited twice (no loop)<br>✅ 404 recorded<br>✅ timeout recorded<br>✅ kept going after the timeout<br>✅ other pages loaded | PASS |
| (b) | 3 | `/ 200`<br>`/t7/a 200`<br>`/t7/missing 404` | ✅ finished without crashing<br>✅ stopped at the page cap (3)<br>✅ started at /<br>✅ no page visited twice | PASS |

**Test 7, crawl part ((a), (b)): PASS**

The test site: `/` links to `/t7/a`, `/t7/missing` (404) and `/t7/slow` (answers after the timeout); `/t7/a` → `/t7/b` → back to `/t7/a` and `/` (a cycle). Outputs and what each scraper printed are in `outputs/`. The stub-model part for (c) is separate (Sun Nov 29).
