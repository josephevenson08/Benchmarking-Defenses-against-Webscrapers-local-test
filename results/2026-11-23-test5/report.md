# Test 5: poisoning hides real values

Run 2026-11-23T13:13:59 · commit 910ee22 · condition `poisoned` · read at 0 s (right after load) and 3 s after load

**PASS**

| Check | Result | |
|---|---|---|
| 1. Fakes file: one valid fake per field, each different from the real value | 70 of 70 fakes | PASS |
| 2. No real value in any page's HTML | 0 real values found (each item page searched for its own values, the other 2 pages for all 70) | PASS |
| 3. Every field shows its fake at 0 s | 70 of 70 | PASS |
| 4. Every field shows its real value at 3 s | 70 of 70 | PASS |


## Each item page

| Page | Fakes at 0 s | Real at 3 s | Values last changed | Fetched its real values | Fields not as expected |
|---|---|---|---|---|---|
| /products/p1 | 10/10 | 10/10 | 2.03 s after start (2.01 s after load) | yes (200) | — |
| /products/p2 | 10/10 | 10/10 | 2.02 s after start (2.01 s after load) | yes (200) | — |
| /products/p3 | 10/10 | 10/10 | 2.03 s after start (2.01 s after load) | yes (200) | — |
| /products/p4 | 10/10 | 10/10 | 2.03 s after start (2.01 s after load) | yes (200) | — |
| /products/p5 | 10/10 | 10/10 | 2.02 s after start (2.01 s after load) | yes (200) | — |
| /products/p6 | 10/10 | 10/10 | 2.03 s after start (2.01 s after load) | yes (200) | — |
| /articles/a1 | 5/5 | 5/5 | 2.03 s after start (2.02 s after load) | yes (200) | — |
| /articles/a2 | 5/5 | 5/5 | 2.02 s after start (2.01 s after load) | yes (200) | — |

Fakes stay on screen until 2.03 s after the page starts loading (mean 2.03 s; config `poison_swap_delay_seconds` = 2).
