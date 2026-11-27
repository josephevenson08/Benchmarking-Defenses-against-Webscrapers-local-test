# False-positive check: a human-like visitor on the trap sites

Run 2026-11-27T18:03:03 · commit 8e61322 · 20 sessions per site · 6 clicks each · 0.5 s pause before each click

The visitor clicks only links a person can see, at random, and never reads robots.txt.

| Site | Sessions caught | False-positive rate | What catches it | |
|---|---|---|---|---|
| honeypot | 0 of 20 | 0% | requested the trap path | PASS (expected 0) |
| tarpit | 15 of 20 | 75% | requested a /maze/ page | reported |

Tarpit: 15 visitors clicked the visible entrance link. In the maze they loaded 4.1 pages and spent 10.0 s on average (each maze page answers after the tarpit's delay).

## Each session

| Session | Pages clicked through | Trap hits | Maze pages |
|---|---|---|---|
| `human-honeypot-1` | / → /products/ → /products/p1 → / → /articles/a1 → /products/ → /products/p2 | 0 | 0 |
| `human-honeypot-2` | / → /products/ → /products/p6 → /products/ → /products/p3 → /products/ → /products/p2 | 0 | 0 |
| `human-honeypot-3` | / → / → /articles/a1 → / → / → /articles/a1 → /products/ | 0 | 0 |
| `human-honeypot-4` | / → / → /articles/a2 → / → /products/ → /products/p4 → /products/ | 0 | 0 |
| `human-honeypot-5` | / → /products/ → /products/p5 → / → /articles/a1 → / → /articles/a1 | 0 | 0 |
| `human-honeypot-6` | / → /articles/a2 → / → /products/ → /products/p5 → /products/ → /products/p2 | 0 | 0 |
| `human-honeypot-7` | / → / → /articles/a2 → /products/ → /products/p3 → /products/ → /products/p3 | 0 | 0 |
| `human-honeypot-8` | / → /articles/a2 → /products/ → /products/p2 → /products/ → /products/p4 → / | 0 | 0 |
| `human-honeypot-9` | / → /articles/a2 → /products/ → / → /articles/a2 → / → /articles/a1 | 0 | 0 |
| `human-honeypot-10` | / → /articles/a1 → /products/ → /products/p5 → /products/ → /products/p5 → / | 0 | 0 |
| `human-honeypot-11` | / → /products/ → / → /articles/a1 → / → /products/ → / | 0 | 0 |
| `human-honeypot-12` | / → /articles/a2 → / → / → / → /articles/a1 → /products/ | 0 | 0 |
| `human-honeypot-13` | / → /products/ → / → / → /articles/a2 → / → /products/ | 0 | 0 |
| `human-honeypot-14` | / → /articles/a2 → /products/ → /products/p1 → / → /products/ → /products/p3 | 0 | 0 |
| `human-honeypot-15` | / → /articles/a1 → /products/ → /products/p3 → /products/ → /products/p1 → /products/ | 0 | 0 |
| `human-honeypot-16` | / → /articles/a1 → /products/ → /products/p5 → / → /articles/a2 → /products/ | 0 | 0 |
| `human-honeypot-17` | / → /articles/a1 → / → /articles/a2 → / → /products/ → /products/p6 | 0 | 0 |
| `human-honeypot-18` | / → /articles/a1 → / → /products/ → /products/p3 → / → / | 0 | 0 |
| `human-honeypot-19` | / → /articles/a1 → /products/ → /products/p1 → / → /products/ → / | 0 | 0 |
| `human-honeypot-20` | / → /articles/a1 → / → / → /products/ → /products/p3 → / | 0 | 0 |
| `human-tarpit-1` | / → /products/ → /maze/start → /maze/ff85cdf0 → /maze/20be2615 → /maze/7429d827 → /maze/f7bb1253 | 0 | 5 |
| `human-tarpit-2` | / → /products/ → /products/p5 → /maze/start → /maze/2622fc0 → /maze/c600a7b7 → /maze/fed15c92 | 0 | 4 |
| `human-tarpit-3` | / → /products/ → /products/p4 → /maze/start → /maze/41fdada6 → /maze/d63a0a81 → /maze/7181bd06 | 0 | 4 |
| `human-tarpit-4` | / → /articles/a2 → /products/ → /products/p5 → /maze/start → /maze/2622fc0 → /maze/ea2629e2 | 0 | 3 |
| `human-tarpit-5` | / → /articles/a2 → /maze/start → /maze/41fdada6 → /maze/958044d → /maze/cd50d4c → /maze/7dd74ec3 | 0 | 5 |
| `human-tarpit-6` | / → /articles/a2 → /maze/start → /maze/41fdada6 → /maze/d63a0a81 → /maze/7181bd06 → /maze/e65d970 | 0 | 5 |
| `human-tarpit-7` | / → /articles/a2 → /products/ → / → /products/ → /products/p2 → /products/ | 0 | 0 |
| `human-tarpit-8` | / → /articles/a2 → /products/ → /products/p2 → / → /articles/a1 → /maze/start | 0 | 1 |
| `human-tarpit-9` | / → /maze/start → /maze/2622fc0 → /maze/b8440979 → /maze/e226f887 → /maze/aa040d12 → /maze/7049d735 | 0 | 6 |
| `human-tarpit-10` | / → /articles/a1 → /products/ → /products/p6 → /maze/start → /maze/db9a2bbe → /maze/ee973e82 | 0 | 3 |
| `human-tarpit-11` | / → /products/ → / → /articles/a1 → /products/ → /products/p4 → /maze/start | 0 | 1 |
| `human-tarpit-12` | / → /articles/a2 → /products/ → /maze/start → /maze/db9a2bbe → /maze/feaa1b5b → /maze/ee8a8109 | 0 | 4 |
| `human-tarpit-13` | / → /maze/start → /maze/db9a2bbe → /maze/feaa1b5b → /maze/4aefb280 → /maze/19ca5e7e → /maze/84dc6461 | 0 | 6 |
| `human-tarpit-14` | / → /products/ → /products/ → /products/p3 → / → /products/ → /products/p3 | 0 | 0 |
| `human-tarpit-15` | / → / → /maze/start → /maze/97fab824 → /maze/a5f23566 → /maze/a0831256 → /maze/eb6961ad | 0 | 5 |
| `human-tarpit-16` | / → / → /maze/start → /maze/97fab824 → /maze/89df81f8 → /maze/d13e556b → /maze/95166c7c | 0 | 5 |
| `human-tarpit-17` | / → /articles/a1 → /maze/start → /maze/41fdada6 → /maze/d63a0a81 → /maze/c74fa3a8 → /maze/f139c799 | 0 | 5 |
| `human-tarpit-18` | / → / → /products/ → /products/ → /products/p2 → / → /articles/a2 | 0 | 0 |
| `human-tarpit-19` | / → /articles/a2 → /products/ → /products/ → /products/ → /products/ → / | 0 | 0 |
| `human-tarpit-20` | / → /products/ → /products/p3 → / → /products/ → /products/p6 → /products/ | 0 | 0 |
