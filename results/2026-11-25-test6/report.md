# Test 6: honeypot and logging

Run 2026-11-25T10:47:57 · commit fb007e2 · trap path `/trap` · run ID R = `test6`

## Part A: Test 6 (requests and log)

| Check | Result | |
|---|---|---|
| Trap request with run R logs as a hit for R | 1 line, 1 hit | PASS |
| Normal page with run R is not a hit | 1 line, 0 hits | PASS |
| Request with no User-Agent logs as `unknown` | 1 line, user_agent empty in 1 | PASS |
| Server stays up (a request afterwards gets 200) | yes | PASS |
| No other run is logged as a hit | 0 | PASS |
| Tarpit part (robots.txt and `/maze/`) | see Part C | PASS |

**Test 6: PASS**  (full request log: `requests.jsonl`)

## Part B: honeypot pages

| Check | Result | |
|---|---|---|
| Exactly one trap link on every page | 10 of 10 pages | PASS |
| The browser does not show it | 10 of 10 hidden | PASS |
| Pixel difference from baseline at most 1.0% | max 0.000%, mean 0.000% | PASS |

**Honeypot pages: PASS**

## Part C: tarpit (a scraper that obeys robots.txt never requests /maze/; one that ignores it does)

robots.txt disallows `/maze/`: yes | PASS

| Run | robots.txt | Exit | Requests | /maze/ requests | Expected | |
|---|---|---|---|---|---|---|
| `test6-obey-a` | obey | 0 | 11 | 0 | none | PASS |
| `test6-obey-b` | obey | 0 | 11 | 0 | none | PASS |
| `test6-obey-d` | obey | 0 | 11 | 0 | none | PASS |
| `test6-ignore-a` | ignore | 0 | 16 | 5 | at least one | PASS |

**Tarpit part: PASS**  (request log: `tarpit.jsonl`)
