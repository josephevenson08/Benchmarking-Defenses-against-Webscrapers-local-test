# Test 7, fake-model part: scraper (c)'s failure rules

Run 2026-11-27T12:30:34 · commit 710fa59 · fake Ollama on 127.0.0.1:11434 · slow answer after 125 s

**PASS**

## Run 1: fake model, whole site

Exit 0 · 121.6 s · pages visited 10 of 15 (cap) · finished

| Page | Fake model's answer | Expected | (c) recorded | Values saved | |
|---|---|---|---|---|---|
| /products/p1 | a list | invalid_json | invalid_json | 0 | PASS |
| /products/p2 | a field missing | missing_key | missing_key | 0 | PASS |
| /products/p3 | after 125 s | model_timeout | model_timeout | 0 | PASS |
| /products/p4 | good | no error | no error | 10 | PASS |
| /products/p5 | good | no error | no error | 10 | PASS |
| /products/p6 | good | no error | no error | 10 | PASS |
| /articles/a1 | good | no error | no error | 5 | PASS |
| /articles/a2 | not JSON | invalid_json | invalid_json | 0 | PASS |

## Run 2: no model running, first 4 pages

Exit 0 · 5.3 s · pages visited 4 of 4 (cap) · finished

| Page | Fake model's answer | Expected | (c) recorded | Values saved | |
|---|---|---|---|---|---|
| /articles/a1 | no model running | model_error | model_error | 0 | PASS |
| /articles/a2 | no model running | model_error | model_error | 0 | PASS |

Each run's output and printed log are in this folder (`test7-model-*.json`, `.log`).
