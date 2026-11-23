# Cross-check of the results

Run 2026-11-23T19:22:27 · runs: `results/2026-11-18-experiment`, `results/2026-11-18-c-all`, `results/2026-11-20-d-all`, `results/2026-11-23-poisoned-2` · results: `results/2026-11-23-results-all` · user cost: `results/2026-11-20-user-cost-full`

**707 of 707 checks agree.**

## Tally for each scraper and defense (recounted from the raw outputs and logs)

| Scraper and site | Correct per run (of 70) | Wrong | of which fakes | Missing | Trap hits | Drop in recall | Verdict | Detection |
|---|---|---|---|---|---|---|---|---|
| (a) on baseline | 70 70 70 | 0 0 0 | 0 0 0 | 0 0 0 | 0 0 0 | — | baseline | 0.00 |
| (a) on shuffled | 4 4 4 | 62 62 62 | 0 0 0 | 4 4 4 | 0 0 0 | 94.3% | stops | 0.00 |
| (a) on honeypot | 70 70 70 | 0 0 0 | 0 0 0 | 0 0 0 | 1 1 1 | 0.0% | no effect | 1.00 |
| (a) on poisoned | 0 0 0 | 70 70 70 | 70 70 70 | 0 0 0 | 0 0 0 | 100.0% | stops | 0.00 |
| (b) on baseline | 70 70 70 | 0 0 0 | 0 0 0 | 0 0 0 | 0 0 0 | — | baseline | 0.00 |
| (b) on shuffled | 4 4 4 | 62 62 62 | 0 0 0 | 4 4 4 | 0 0 0 | 94.3% | stops | 0.00 |
| (b) on honeypot | 70 70 70 | 0 0 0 | 0 0 0 | 0 0 0 | 1 1 1 | 0.0% | no effect | 1.00 |
| (b) on poisoned | 0 0 0 | 70 70 70 | 70 70 70 | 0 0 0 | 0 0 0 | 100.0% | stops | 0.00 |
| (c) on baseline | 70 70 70 | 0 0 0 | 0 0 0 | 0 0 0 | 0 0 0 | — | baseline | 0.00 |
| (c) on shuffled | 48 49 49 | 13 11 11 | 0 0 0 | 9 10 10 | 0 0 0 | 30.5% | reduces | 0.00 |
| (c) on honeypot | 70 70 70 | 0 0 0 | 0 0 0 | 0 0 0 | 1 1 1 | 0.0% | no effect | 1.00 |
| (c) on poisoned | 0 0 0 | 70 70 70 | 70 70 70 | 0 0 0 | 0 0 0 | 100.0% | stops | 0.00 |
| (d) on baseline | 70 70 70 | 0 0 0 | 0 0 0 | 0 0 0 | 0 0 0 | — | baseline | 0.00 |
| (d) on shuffled | 70 70 70 | 0 0 0 | 0 0 0 | 0 0 0 | 0 0 0 | 0.0% | no effect | 0.00 |
| (d) on honeypot | 70 70 70 | 0 0 0 | 0 0 0 | 0 0 0 | 0 0 0 | 0.0% | no effect | 0.00 |
| (d) on poisoned | 70 70 70 | 0 0 0 | 0 0 0 | 0 0 0 | 0 0 0 | 0.0% | no effect | 0.00 |

## Every check

| Check | Agrees | Detail |
|---|---|---|
| independent counter on the Test 2 fixture: 63 correct, 4 wrong (2 fakes, 1 malformed), 3 missing | yes | got 63 correct, 4 wrong (2 fakes, 1 malformed), 3 missing |
| 2026-11-18-experiment logs/baseline.jsonl: every request is from a baseline run | yes | 66 requests |
| a-baseline-1: output names the right run and scraper | yes | run_id a-baseline-1, scraper a |
| a-baseline-1: in results.csv | yes |  |
| a-baseline-1: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| a-baseline-1: precision | yes | recounted 1.0, reported 1.0 |
| a-baseline-1: F1 | yes | recounted 1.0, reported 1.0 |
| a-baseline-1: honeypot hits | yes | recounted 0, reported 0 |
| a-baseline-1: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| a-baseline-1: every request carries the run ID | yes | 11 requests |
| a-baseline-1: time per page | yes | recounted 0.014299999999999998, reported 0.0143 |
| a-baseline-2: output names the right run and scraper | yes | run_id a-baseline-2, scraper a |
| a-baseline-2: in results.csv | yes |  |
| a-baseline-2: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| a-baseline-2: precision | yes | recounted 1.0, reported 1.0 |
| a-baseline-2: F1 | yes | recounted 1.0, reported 1.0 |
| a-baseline-2: honeypot hits | yes | recounted 0, reported 0 |
| a-baseline-2: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| a-baseline-2: every request carries the run ID | yes | 11 requests |
| a-baseline-2: time per page | yes | recounted 0.0089, reported 0.0089 |
| a-baseline-3: output names the right run and scraper | yes | run_id a-baseline-3, scraper a |
| a-baseline-3: in results.csv | yes |  |
| a-baseline-3: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| a-baseline-3: precision | yes | recounted 1.0, reported 1.0 |
| a-baseline-3: F1 | yes | recounted 1.0, reported 1.0 |
| a-baseline-3: honeypot hits | yes | recounted 0, reported 0 |
| a-baseline-3: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| a-baseline-3: every request carries the run ID | yes | 11 requests |
| a-baseline-3: time per page | yes | recounted 0.0128, reported 0.0128 |
| b-baseline-1: output names the right run and scraper | yes | run_id b-baseline-1, scraper b |
| b-baseline-1: in results.csv | yes |  |
| b-baseline-1: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| b-baseline-1: precision | yes | recounted 1.0, reported 1.0 |
| b-baseline-1: F1 | yes | recounted 1.0, reported 1.0 |
| b-baseline-1: honeypot hits | yes | recounted 0, reported 0 |
| b-baseline-1: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| b-baseline-1: every request carries the run ID | yes | 11 requests |
| b-baseline-1: time per page | yes | recounted 0.023200000000000002, reported 0.0232 |
| b-baseline-2: output names the right run and scraper | yes | run_id b-baseline-2, scraper b |
| b-baseline-2: in results.csv | yes |  |
| b-baseline-2: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| b-baseline-2: precision | yes | recounted 1.0, reported 1.0 |
| b-baseline-2: F1 | yes | recounted 1.0, reported 1.0 |
| b-baseline-2: honeypot hits | yes | recounted 0, reported 0 |
| b-baseline-2: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| b-baseline-2: every request carries the run ID | yes | 11 requests |
| b-baseline-2: time per page | yes | recounted 0.0224, reported 0.0224 |
| b-baseline-3: output names the right run and scraper | yes | run_id b-baseline-3, scraper b |
| b-baseline-3: in results.csv | yes |  |
| b-baseline-3: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| b-baseline-3: precision | yes | recounted 1.0, reported 1.0 |
| b-baseline-3: F1 | yes | recounted 1.0, reported 1.0 |
| b-baseline-3: honeypot hits | yes | recounted 0, reported 0 |
| b-baseline-3: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| b-baseline-3: every request carries the run ID | yes | 11 requests |
| b-baseline-3: time per page | yes | recounted 0.0235, reported 0.0235 |
| 2026-11-18-experiment logs/shuffled.jsonl: every request is from a shuffled run | yes | 66 requests |
| a-shuffled-1: output names the right run and scraper | yes | run_id a-shuffled-1, scraper a |
| a-shuffled-1: in results.csv | yes |  |
| a-shuffled-1: correct / wrong / missing | yes | recounted 4/62/4, reported 4/62/4 |
| a-shuffled-1: precision | yes | recounted 0.06060606060606061, reported 0.0606061 |
| a-shuffled-1: F1 | yes | recounted 0.05882352941176471, reported 0.0588235 |
| a-shuffled-1: honeypot hits | yes | recounted 0, reported 0 |
| a-shuffled-1: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| a-shuffled-1: every request carries the run ID | yes | 11 requests |
| a-shuffled-1: time per page | yes | recounted 0.014599999999999998, reported 0.0146 |
| a-shuffled-2: output names the right run and scraper | yes | run_id a-shuffled-2, scraper a |
| a-shuffled-2: in results.csv | yes |  |
| a-shuffled-2: correct / wrong / missing | yes | recounted 4/62/4, reported 4/62/4 |
| a-shuffled-2: precision | yes | recounted 0.06060606060606061, reported 0.0606061 |
| a-shuffled-2: F1 | yes | recounted 0.05882352941176471, reported 0.0588235 |
| a-shuffled-2: honeypot hits | yes | recounted 0, reported 0 |
| a-shuffled-2: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| a-shuffled-2: every request carries the run ID | yes | 11 requests |
| a-shuffled-2: time per page | yes | recounted 0.0149, reported 0.0149 |
| a-shuffled-3: output names the right run and scraper | yes | run_id a-shuffled-3, scraper a |
| a-shuffled-3: in results.csv | yes |  |
| a-shuffled-3: correct / wrong / missing | yes | recounted 4/62/4, reported 4/62/4 |
| a-shuffled-3: precision | yes | recounted 0.06060606060606061, reported 0.0606061 |
| a-shuffled-3: F1 | yes | recounted 0.05882352941176471, reported 0.0588235 |
| a-shuffled-3: honeypot hits | yes | recounted 0, reported 0 |
| a-shuffled-3: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| a-shuffled-3: every request carries the run ID | yes | 11 requests |
| a-shuffled-3: time per page | yes | recounted 0.0178, reported 0.0178 |
| b-shuffled-1: output names the right run and scraper | yes | run_id b-shuffled-1, scraper b |
| b-shuffled-1: in results.csv | yes |  |
| b-shuffled-1: correct / wrong / missing | yes | recounted 4/62/4, reported 4/62/4 |
| b-shuffled-1: precision | yes | recounted 0.06060606060606061, reported 0.0606061 |
| b-shuffled-1: F1 | yes | recounted 0.05882352941176471, reported 0.0588235 |
| b-shuffled-1: honeypot hits | yes | recounted 0, reported 0 |
| b-shuffled-1: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| b-shuffled-1: every request carries the run ID | yes | 11 requests |
| b-shuffled-1: time per page | yes | recounted 0.0242, reported 0.0242 |
| b-shuffled-2: output names the right run and scraper | yes | run_id b-shuffled-2, scraper b |
| b-shuffled-2: in results.csv | yes |  |
| b-shuffled-2: correct / wrong / missing | yes | recounted 4/62/4, reported 4/62/4 |
| b-shuffled-2: precision | yes | recounted 0.06060606060606061, reported 0.0606061 |
| b-shuffled-2: F1 | yes | recounted 0.05882352941176471, reported 0.0588235 |
| b-shuffled-2: honeypot hits | yes | recounted 0, reported 0 |
| b-shuffled-2: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| b-shuffled-2: every request carries the run ID | yes | 11 requests |
| b-shuffled-2: time per page | yes | recounted 0.0217, reported 0.0217 |
| b-shuffled-3: output names the right run and scraper | yes | run_id b-shuffled-3, scraper b |
| b-shuffled-3: in results.csv | yes |  |
| b-shuffled-3: correct / wrong / missing | yes | recounted 4/62/4, reported 4/62/4 |
| b-shuffled-3: precision | yes | recounted 0.06060606060606061, reported 0.0606061 |
| b-shuffled-3: F1 | yes | recounted 0.05882352941176471, reported 0.0588235 |
| b-shuffled-3: honeypot hits | yes | recounted 0, reported 0 |
| b-shuffled-3: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| b-shuffled-3: every request carries the run ID | yes | 11 requests |
| b-shuffled-3: time per page | yes | recounted 0.020399999999999998, reported 0.0204 |
| 2026-11-18-experiment logs/honeypot.jsonl: every request is from a honeypot run | yes | 72 requests |
| a-honeypot-1: output names the right run and scraper | yes | run_id a-honeypot-1, scraper a |
| a-honeypot-1: in results.csv | yes |  |
| a-honeypot-1: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| a-honeypot-1: precision | yes | recounted 1.0, reported 1.0 |
| a-honeypot-1: F1 | yes | recounted 1.0, reported 1.0 |
| a-honeypot-1: honeypot hits | yes | recounted 1, reported 1 |
| a-honeypot-1: pages in output = page requests in log | yes | output 11, log 11, reported 11 |
| a-honeypot-1: every request carries the run ID | yes | 12 requests |
| a-honeypot-1: time per page | yes | recounted 0.016636363636363637, reported 0.0166364 |
| a-honeypot-2: output names the right run and scraper | yes | run_id a-honeypot-2, scraper a |
| a-honeypot-2: in results.csv | yes |  |
| a-honeypot-2: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| a-honeypot-2: precision | yes | recounted 1.0, reported 1.0 |
| a-honeypot-2: F1 | yes | recounted 1.0, reported 1.0 |
| a-honeypot-2: honeypot hits | yes | recounted 1, reported 1 |
| a-honeypot-2: pages in output = page requests in log | yes | output 11, log 11, reported 11 |
| a-honeypot-2: every request carries the run ID | yes | 12 requests |
| a-honeypot-2: time per page | yes | recounted 0.015909090909090907, reported 0.0159091 |
| a-honeypot-3: output names the right run and scraper | yes | run_id a-honeypot-3, scraper a |
| a-honeypot-3: in results.csv | yes |  |
| a-honeypot-3: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| a-honeypot-3: precision | yes | recounted 1.0, reported 1.0 |
| a-honeypot-3: F1 | yes | recounted 1.0, reported 1.0 |
| a-honeypot-3: honeypot hits | yes | recounted 1, reported 1 |
| a-honeypot-3: pages in output = page requests in log | yes | output 11, log 11, reported 11 |
| a-honeypot-3: every request carries the run ID | yes | 12 requests |
| a-honeypot-3: time per page | yes | recounted 0.018909090909090907, reported 0.0189091 |
| b-honeypot-1: output names the right run and scraper | yes | run_id b-honeypot-1, scraper b |
| b-honeypot-1: in results.csv | yes |  |
| b-honeypot-1: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| b-honeypot-1: precision | yes | recounted 1.0, reported 1.0 |
| b-honeypot-1: F1 | yes | recounted 1.0, reported 1.0 |
| b-honeypot-1: honeypot hits | yes | recounted 1, reported 1 |
| b-honeypot-1: pages in output = page requests in log | yes | output 11, log 11, reported 11 |
| b-honeypot-1: every request carries the run ID | yes | 12 requests |
| b-honeypot-1: time per page | yes | recounted 0.022545454545454546, reported 0.0225455 |
| b-honeypot-2: output names the right run and scraper | yes | run_id b-honeypot-2, scraper b |
| b-honeypot-2: in results.csv | yes |  |
| b-honeypot-2: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| b-honeypot-2: precision | yes | recounted 1.0, reported 1.0 |
| b-honeypot-2: F1 | yes | recounted 1.0, reported 1.0 |
| b-honeypot-2: honeypot hits | yes | recounted 1, reported 1 |
| b-honeypot-2: pages in output = page requests in log | yes | output 11, log 11, reported 11 |
| b-honeypot-2: every request carries the run ID | yes | 12 requests |
| b-honeypot-2: time per page | yes | recounted 0.022818181818181817, reported 0.0228182 |
| b-honeypot-3: output names the right run and scraper | yes | run_id b-honeypot-3, scraper b |
| b-honeypot-3: in results.csv | yes |  |
| b-honeypot-3: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| b-honeypot-3: precision | yes | recounted 1.0, reported 1.0 |
| b-honeypot-3: F1 | yes | recounted 1.0, reported 1.0 |
| b-honeypot-3: honeypot hits | yes | recounted 1, reported 1 |
| b-honeypot-3: pages in output = page requests in log | yes | output 11, log 11, reported 11 |
| b-honeypot-3: every request carries the run ID | yes | 12 requests |
| b-honeypot-3: time per page | yes | recounted 0.021363636363636362, reported 0.0213636 |
| 2026-11-18-c-all logs/baseline.jsonl: every request is from a baseline run | yes | 33 requests |
| c-baseline-1: output names the right run and scraper | yes | run_id c-baseline-1, scraper c |
| c-baseline-1: in results.csv | yes |  |
| c-baseline-1: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| c-baseline-1: precision | yes | recounted 1.0, reported 1.0 |
| c-baseline-1: F1 | yes | recounted 1.0, reported 1.0 |
| c-baseline-1: honeypot hits | yes | recounted 0, reported 0 |
| c-baseline-1: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| c-baseline-1: every request carries the run ID | yes | 11 requests |
| c-baseline-1: time per page | yes | recounted 6.878400000000001, reported 6.8784 |
| c-baseline-2: output names the right run and scraper | yes | run_id c-baseline-2, scraper c |
| c-baseline-2: in results.csv | yes |  |
| c-baseline-2: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| c-baseline-2: precision | yes | recounted 1.0, reported 1.0 |
| c-baseline-2: F1 | yes | recounted 1.0, reported 1.0 |
| c-baseline-2: honeypot hits | yes | recounted 0, reported 0 |
| c-baseline-2: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| c-baseline-2: every request carries the run ID | yes | 11 requests |
| c-baseline-2: time per page | yes | recounted 5.1327, reported 5.1327 |
| c-baseline-3: output names the right run and scraper | yes | run_id c-baseline-3, scraper c |
| c-baseline-3: in results.csv | yes |  |
| c-baseline-3: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| c-baseline-3: precision | yes | recounted 1.0, reported 1.0 |
| c-baseline-3: F1 | yes | recounted 1.0, reported 1.0 |
| c-baseline-3: honeypot hits | yes | recounted 0, reported 0 |
| c-baseline-3: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| c-baseline-3: every request carries the run ID | yes | 11 requests |
| c-baseline-3: time per page | yes | recounted 5.227, reported 5.227 |
| 2026-11-18-c-all logs/shuffled.jsonl: every request is from a shuffled run | yes | 33 requests |
| c-shuffled-1: output names the right run and scraper | yes | run_id c-shuffled-1, scraper c |
| c-shuffled-1: in results.csv | yes |  |
| c-shuffled-1: correct / wrong / missing | yes | recounted 48/13/9, reported 48/13/9 |
| c-shuffled-1: precision | yes | recounted 0.7868852459016393, reported 0.786885 |
| c-shuffled-1: F1 | yes | recounted 0.732824427480916, reported 0.732824 |
| c-shuffled-1: honeypot hits | yes | recounted 0, reported 0 |
| c-shuffled-1: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| c-shuffled-1: every request carries the run ID | yes | 11 requests |
| c-shuffled-1: time per page | yes | recounted 6.4167000000000005, reported 6.4167 |
| c-shuffled-2: output names the right run and scraper | yes | run_id c-shuffled-2, scraper c |
| c-shuffled-2: in results.csv | yes |  |
| c-shuffled-2: correct / wrong / missing | yes | recounted 49/11/10, reported 49/11/10 |
| c-shuffled-2: precision | yes | recounted 0.8166666666666667, reported 0.816667 |
| c-shuffled-2: F1 | yes | recounted 0.7538461538461538, reported 0.753846 |
| c-shuffled-2: honeypot hits | yes | recounted 0, reported 0 |
| c-shuffled-2: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| c-shuffled-2: every request carries the run ID | yes | 11 requests |
| c-shuffled-2: time per page | yes | recounted 4.8134999999999994, reported 4.8135 |
| c-shuffled-3: output names the right run and scraper | yes | run_id c-shuffled-3, scraper c |
| c-shuffled-3: in results.csv | yes |  |
| c-shuffled-3: correct / wrong / missing | yes | recounted 49/11/10, reported 49/11/10 |
| c-shuffled-3: precision | yes | recounted 0.8166666666666667, reported 0.816667 |
| c-shuffled-3: F1 | yes | recounted 0.7538461538461538, reported 0.753846 |
| c-shuffled-3: honeypot hits | yes | recounted 0, reported 0 |
| c-shuffled-3: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| c-shuffled-3: every request carries the run ID | yes | 11 requests |
| c-shuffled-3: time per page | yes | recounted 5.122, reported 5.122 |
| 2026-11-18-c-all logs/honeypot.jsonl: every request is from a honeypot run | yes | 36 requests |
| c-honeypot-1: output names the right run and scraper | yes | run_id c-honeypot-1, scraper c |
| c-honeypot-1: in results.csv | yes |  |
| c-honeypot-1: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| c-honeypot-1: precision | yes | recounted 1.0, reported 1.0 |
| c-honeypot-1: F1 | yes | recounted 1.0, reported 1.0 |
| c-honeypot-1: honeypot hits | yes | recounted 1, reported 1 |
| c-honeypot-1: pages in output = page requests in log | yes | output 11, log 11, reported 11 |
| c-honeypot-1: every request carries the run ID | yes | 12 requests |
| c-honeypot-1: time per page | yes | recounted 5.559454545454546, reported 5.55945 |
| c-honeypot-2: output names the right run and scraper | yes | run_id c-honeypot-2, scraper c |
| c-honeypot-2: in results.csv | yes |  |
| c-honeypot-2: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| c-honeypot-2: precision | yes | recounted 1.0, reported 1.0 |
| c-honeypot-2: F1 | yes | recounted 1.0, reported 1.0 |
| c-honeypot-2: honeypot hits | yes | recounted 1, reported 1 |
| c-honeypot-2: pages in output = page requests in log | yes | output 11, log 11, reported 11 |
| c-honeypot-2: every request carries the run ID | yes | 12 requests |
| c-honeypot-2: time per page | yes | recounted 4.951272727272727, reported 4.95127 |
| c-honeypot-3: output names the right run and scraper | yes | run_id c-honeypot-3, scraper c |
| c-honeypot-3: in results.csv | yes |  |
| c-honeypot-3: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| c-honeypot-3: precision | yes | recounted 1.0, reported 1.0 |
| c-honeypot-3: F1 | yes | recounted 1.0, reported 1.0 |
| c-honeypot-3: honeypot hits | yes | recounted 1, reported 1 |
| c-honeypot-3: pages in output = page requests in log | yes | output 11, log 11, reported 11 |
| c-honeypot-3: every request carries the run ID | yes | 12 requests |
| c-honeypot-3: time per page | yes | recounted 5.557454545454545, reported 5.55745 |
| 2026-11-20-d-all logs/baseline.jsonl: every request is from a baseline run | yes | 33 requests |
| d-baseline-1: output names the right run and scraper | yes | run_id d-baseline-1, scraper d |
| d-baseline-1: in results.csv | yes |  |
| d-baseline-1: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| d-baseline-1: precision | yes | recounted 1.0, reported 1.0 |
| d-baseline-1: F1 | yes | recounted 1.0, reported 1.0 |
| d-baseline-1: honeypot hits | yes | recounted 0, reported 0 |
| d-baseline-1: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| d-baseline-1: every request carries the run ID | yes | 11 requests |
| d-baseline-1: time per page | yes | recounted 3.0375, reported 3.0375 |
| d-baseline-2: output names the right run and scraper | yes | run_id d-baseline-2, scraper d |
| d-baseline-2: in results.csv | yes |  |
| d-baseline-2: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| d-baseline-2: precision | yes | recounted 1.0, reported 1.0 |
| d-baseline-2: F1 | yes | recounted 1.0, reported 1.0 |
| d-baseline-2: honeypot hits | yes | recounted 0, reported 0 |
| d-baseline-2: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| d-baseline-2: every request carries the run ID | yes | 11 requests |
| d-baseline-2: time per page | yes | recounted 3.0346, reported 3.0346 |
| d-baseline-3: output names the right run and scraper | yes | run_id d-baseline-3, scraper d |
| d-baseline-3: in results.csv | yes |  |
| d-baseline-3: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| d-baseline-3: precision | yes | recounted 1.0, reported 1.0 |
| d-baseline-3: F1 | yes | recounted 1.0, reported 1.0 |
| d-baseline-3: honeypot hits | yes | recounted 0, reported 0 |
| d-baseline-3: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| d-baseline-3: every request carries the run ID | yes | 11 requests |
| d-baseline-3: time per page | yes | recounted 3.032, reported 3.032 |
| 2026-11-20-d-all logs/shuffled.jsonl: every request is from a shuffled run | yes | 33 requests |
| d-shuffled-1: output names the right run and scraper | yes | run_id d-shuffled-1, scraper d |
| d-shuffled-1: in results.csv | yes |  |
| d-shuffled-1: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| d-shuffled-1: precision | yes | recounted 1.0, reported 1.0 |
| d-shuffled-1: F1 | yes | recounted 1.0, reported 1.0 |
| d-shuffled-1: honeypot hits | yes | recounted 0, reported 0 |
| d-shuffled-1: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| d-shuffled-1: every request carries the run ID | yes | 11 requests |
| d-shuffled-1: time per page | yes | recounted 3.037, reported 3.037 |
| d-shuffled-2: output names the right run and scraper | yes | run_id d-shuffled-2, scraper d |
| d-shuffled-2: in results.csv | yes |  |
| d-shuffled-2: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| d-shuffled-2: precision | yes | recounted 1.0, reported 1.0 |
| d-shuffled-2: F1 | yes | recounted 1.0, reported 1.0 |
| d-shuffled-2: honeypot hits | yes | recounted 0, reported 0 |
| d-shuffled-2: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| d-shuffled-2: every request carries the run ID | yes | 11 requests |
| d-shuffled-2: time per page | yes | recounted 3.0381, reported 3.0381 |
| d-shuffled-3: output names the right run and scraper | yes | run_id d-shuffled-3, scraper d |
| d-shuffled-3: in results.csv | yes |  |
| d-shuffled-3: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| d-shuffled-3: precision | yes | recounted 1.0, reported 1.0 |
| d-shuffled-3: F1 | yes | recounted 1.0, reported 1.0 |
| d-shuffled-3: honeypot hits | yes | recounted 0, reported 0 |
| d-shuffled-3: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| d-shuffled-3: every request carries the run ID | yes | 11 requests |
| d-shuffled-3: time per page | yes | recounted 3.0362999999999998, reported 3.0363 |
| 2026-11-20-d-all logs/honeypot.jsonl: every request is from a honeypot run | yes | 33 requests |
| d-honeypot-1: output names the right run and scraper | yes | run_id d-honeypot-1, scraper d |
| d-honeypot-1: in results.csv | yes |  |
| d-honeypot-1: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| d-honeypot-1: precision | yes | recounted 1.0, reported 1.0 |
| d-honeypot-1: F1 | yes | recounted 1.0, reported 1.0 |
| d-honeypot-1: honeypot hits | yes | recounted 0, reported 0 |
| d-honeypot-1: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| d-honeypot-1: every request carries the run ID | yes | 11 requests |
| d-honeypot-1: time per page | yes | recounted 3.0353000000000003, reported 3.0353 |
| d-honeypot-2: output names the right run and scraper | yes | run_id d-honeypot-2, scraper d |
| d-honeypot-2: in results.csv | yes |  |
| d-honeypot-2: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| d-honeypot-2: precision | yes | recounted 1.0, reported 1.0 |
| d-honeypot-2: F1 | yes | recounted 1.0, reported 1.0 |
| d-honeypot-2: honeypot hits | yes | recounted 0, reported 0 |
| d-honeypot-2: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| d-honeypot-2: every request carries the run ID | yes | 11 requests |
| d-honeypot-2: time per page | yes | recounted 3.0353000000000003, reported 3.0353 |
| d-honeypot-3: output names the right run and scraper | yes | run_id d-honeypot-3, scraper d |
| d-honeypot-3: in results.csv | yes |  |
| d-honeypot-3: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| d-honeypot-3: precision | yes | recounted 1.0, reported 1.0 |
| d-honeypot-3: F1 | yes | recounted 1.0, reported 1.0 |
| d-honeypot-3: honeypot hits | yes | recounted 0, reported 0 |
| d-honeypot-3: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| d-honeypot-3: every request carries the run ID | yes | 11 requests |
| d-honeypot-3: time per page | yes | recounted 3.0381, reported 3.0381 |
| 2026-11-23-poisoned-2 logs/poisoned.jsonl: every request is from a poisoned run | yes | 180 requests |
| a-poisoned-1: output names the right run and scraper | yes | run_id a-poisoned-1, scraper a |
| a-poisoned-1: in results.csv | yes |  |
| a-poisoned-1: correct / wrong / missing | yes | recounted 0/70/0, reported 0/70/0 |
| a-poisoned-1: precision | yes | recounted 0.0, reported 0.0 |
| a-poisoned-1: F1 | yes | recounted 0.0, reported 0.0 |
| a-poisoned-1: honeypot hits | yes | recounted 0, reported 0 |
| a-poisoned-1: fakes | yes | recounted 70, reported 70 |
| a-poisoned-1: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| a-poisoned-1: every request carries the run ID | yes | 11 requests |
| a-poisoned-1: time per page | yes | recounted 0.020399999999999998, reported 0.0204 |
| a-poisoned-2: output names the right run and scraper | yes | run_id a-poisoned-2, scraper a |
| a-poisoned-2: in results.csv | yes |  |
| a-poisoned-2: correct / wrong / missing | yes | recounted 0/70/0, reported 0/70/0 |
| a-poisoned-2: precision | yes | recounted 0.0, reported 0.0 |
| a-poisoned-2: F1 | yes | recounted 0.0, reported 0.0 |
| a-poisoned-2: honeypot hits | yes | recounted 0, reported 0 |
| a-poisoned-2: fakes | yes | recounted 70, reported 70 |
| a-poisoned-2: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| a-poisoned-2: every request carries the run ID | yes | 11 requests |
| a-poisoned-2: time per page | yes | recounted 0.0161, reported 0.0161 |
| a-poisoned-3: output names the right run and scraper | yes | run_id a-poisoned-3, scraper a |
| a-poisoned-3: in results.csv | yes |  |
| a-poisoned-3: correct / wrong / missing | yes | recounted 0/70/0, reported 0/70/0 |
| a-poisoned-3: precision | yes | recounted 0.0, reported 0.0 |
| a-poisoned-3: F1 | yes | recounted 0.0, reported 0.0 |
| a-poisoned-3: honeypot hits | yes | recounted 0, reported 0 |
| a-poisoned-3: fakes | yes | recounted 70, reported 70 |
| a-poisoned-3: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| a-poisoned-3: every request carries the run ID | yes | 11 requests |
| a-poisoned-3: time per page | yes | recounted 0.017599999999999998, reported 0.0176 |
| b-poisoned-1: output names the right run and scraper | yes | run_id b-poisoned-1, scraper b |
| b-poisoned-1: in results.csv | yes |  |
| b-poisoned-1: correct / wrong / missing | yes | recounted 0/70/0, reported 0/70/0 |
| b-poisoned-1: precision | yes | recounted 0.0, reported 0.0 |
| b-poisoned-1: F1 | yes | recounted 0.0, reported 0.0 |
| b-poisoned-1: honeypot hits | yes | recounted 0, reported 0 |
| b-poisoned-1: fakes | yes | recounted 70, reported 70 |
| b-poisoned-1: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| b-poisoned-1: every request carries the run ID | yes | 11 requests |
| b-poisoned-1: time per page | yes | recounted 0.0252, reported 0.0252 |
| b-poisoned-2: output names the right run and scraper | yes | run_id b-poisoned-2, scraper b |
| b-poisoned-2: in results.csv | yes |  |
| b-poisoned-2: correct / wrong / missing | yes | recounted 0/70/0, reported 0/70/0 |
| b-poisoned-2: precision | yes | recounted 0.0, reported 0.0 |
| b-poisoned-2: F1 | yes | recounted 0.0, reported 0.0 |
| b-poisoned-2: honeypot hits | yes | recounted 0, reported 0 |
| b-poisoned-2: fakes | yes | recounted 70, reported 70 |
| b-poisoned-2: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| b-poisoned-2: every request carries the run ID | yes | 11 requests |
| b-poisoned-2: time per page | yes | recounted 0.026000000000000002, reported 0.026 |
| b-poisoned-3: output names the right run and scraper | yes | run_id b-poisoned-3, scraper b |
| b-poisoned-3: in results.csv | yes |  |
| b-poisoned-3: correct / wrong / missing | yes | recounted 0/70/0, reported 0/70/0 |
| b-poisoned-3: precision | yes | recounted 0.0, reported 0.0 |
| b-poisoned-3: F1 | yes | recounted 0.0, reported 0.0 |
| b-poisoned-3: honeypot hits | yes | recounted 0, reported 0 |
| b-poisoned-3: fakes | yes | recounted 70, reported 70 |
| b-poisoned-3: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| b-poisoned-3: every request carries the run ID | yes | 11 requests |
| b-poisoned-3: time per page | yes | recounted 0.025, reported 0.025 |
| c-poisoned-1: output names the right run and scraper | yes | run_id c-poisoned-1, scraper c |
| c-poisoned-1: in results.csv | yes |  |
| c-poisoned-1: correct / wrong / missing | yes | recounted 0/70/0, reported 0/70/0 |
| c-poisoned-1: precision | yes | recounted 0.0, reported 0.0 |
| c-poisoned-1: F1 | yes | recounted 0.0, reported 0.0 |
| c-poisoned-1: honeypot hits | yes | recounted 0, reported 0 |
| c-poisoned-1: fakes | yes | recounted 70, reported 70 |
| c-poisoned-1: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| c-poisoned-1: every request carries the run ID | yes | 19 requests |
| c-poisoned-1: time per page | yes | recounted 6.436400000000001, reported 6.4364 |
| c-poisoned-2: output names the right run and scraper | yes | run_id c-poisoned-2, scraper c |
| c-poisoned-2: in results.csv | yes |  |
| c-poisoned-2: correct / wrong / missing | yes | recounted 0/70/0, reported 0/70/0 |
| c-poisoned-2: precision | yes | recounted 0.0, reported 0.0 |
| c-poisoned-2: F1 | yes | recounted 0.0, reported 0.0 |
| c-poisoned-2: honeypot hits | yes | recounted 0, reported 0 |
| c-poisoned-2: fakes | yes | recounted 70, reported 70 |
| c-poisoned-2: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| c-poisoned-2: every request carries the run ID | yes | 19 requests |
| c-poisoned-2: time per page | yes | recounted 5.1423000000000005, reported 5.1423 |
| c-poisoned-3: output names the right run and scraper | yes | run_id c-poisoned-3, scraper c |
| c-poisoned-3: in results.csv | yes |  |
| c-poisoned-3: correct / wrong / missing | yes | recounted 0/70/0, reported 0/70/0 |
| c-poisoned-3: precision | yes | recounted 0.0, reported 0.0 |
| c-poisoned-3: F1 | yes | recounted 0.0, reported 0.0 |
| c-poisoned-3: honeypot hits | yes | recounted 0, reported 0 |
| c-poisoned-3: fakes | yes | recounted 70, reported 70 |
| c-poisoned-3: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| c-poisoned-3: every request carries the run ID | yes | 19 requests |
| c-poisoned-3: time per page | yes | recounted 5.1156999999999995, reported 5.1157 |
| d-poisoned-1: output names the right run and scraper | yes | run_id d-poisoned-1, scraper d |
| d-poisoned-1: in results.csv | yes |  |
| d-poisoned-1: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| d-poisoned-1: precision | yes | recounted 1.0, reported 1.0 |
| d-poisoned-1: F1 | yes | recounted 1.0, reported 1.0 |
| d-poisoned-1: honeypot hits | yes | recounted 0, reported 0 |
| d-poisoned-1: fakes | yes | recounted 0, reported 0 |
| d-poisoned-1: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| d-poisoned-1: every request carries the run ID | yes | 19 requests |
| d-poisoned-1: time per page | yes | recounted 4.6581, reported 4.6581 |
| d-poisoned-2: output names the right run and scraper | yes | run_id d-poisoned-2, scraper d |
| d-poisoned-2: in results.csv | yes |  |
| d-poisoned-2: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| d-poisoned-2: precision | yes | recounted 1.0, reported 1.0 |
| d-poisoned-2: F1 | yes | recounted 1.0, reported 1.0 |
| d-poisoned-2: honeypot hits | yes | recounted 0, reported 0 |
| d-poisoned-2: fakes | yes | recounted 0, reported 0 |
| d-poisoned-2: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| d-poisoned-2: every request carries the run ID | yes | 19 requests |
| d-poisoned-2: time per page | yes | recounted 4.6501, reported 4.6501 |
| d-poisoned-3: output names the right run and scraper | yes | run_id d-poisoned-3, scraper d |
| d-poisoned-3: in results.csv | yes |  |
| d-poisoned-3: correct / wrong / missing | yes | recounted 70/0/0, reported 70/0/0 |
| d-poisoned-3: precision | yes | recounted 1.0, reported 1.0 |
| d-poisoned-3: F1 | yes | recounted 1.0, reported 1.0 |
| d-poisoned-3: honeypot hits | yes | recounted 0, reported 0 |
| d-poisoned-3: fakes | yes | recounted 0, reported 0 |
| d-poisoned-3: pages in output = page requests in log | yes | output 10, log 10, reported 10 |
| d-poisoned-3: every request carries the run ID | yes | 19 requests |
| d-poisoned-3: time per page | yes | recounted 4.6491999999999996, reported 4.6492 |
| same pages and seeds for baseline.manifest.json in every folder | yes | 3 folders |
| same pages and seeds for honeypot.manifest.json in every folder | yes | 3 folders |
| same pages and seeds for shuffled.manifest.json in every folder | yes | 3 folders |
| same pages and seeds for poisoned.manifest.json in every folder | yes | 1 folders |
| (a) on baseline: in cells.csv | yes |  |
| (a) on baseline: correct per run | yes | recounted [70, 70, 70], reported 70 70 70 |
| (a) on baseline: mean recall | yes | recounted 1.0, reported 1.0 |
| (a) on baseline: min recall | yes | recounted 1.0, reported 1.0 |
| (a) on baseline: max recall | yes | recounted 1.0, reported 1.0 |
| (a) on baseline: mean precision | yes | recounted 1.0, reported 1.0 |
| (a) on baseline: mean F1 | yes | recounted 1.0, reported 1.0 |
| (a) on baseline: success rate | yes | recounted 1.0, reported 1.0 |
| (a) on baseline: drop in recall | yes | recounted None, reported None |
| (a) on baseline: verdict | yes | recounted baseline, reported baseline |
| (a) on baseline: detection rate | yes | recounted 0.0, reported 0.0 |
| (a) on shuffled: in cells.csv | yes |  |
| (a) on shuffled: correct per run | yes | recounted [4, 4, 4], reported 4 4 4 |
| (a) on shuffled: mean recall | yes | recounted 0.05714285714285714, reported 0.0571429 |
| (a) on shuffled: min recall | yes | recounted 0.05714285714285714, reported 0.0571429 |
| (a) on shuffled: max recall | yes | recounted 0.05714285714285714, reported 0.0571429 |
| (a) on shuffled: mean precision | yes | recounted 0.06060606060606061, reported 0.0606061 |
| (a) on shuffled: mean F1 | yes | recounted 0.05882352941176471, reported 0.0588235 |
| (a) on shuffled: success rate | yes | recounted 0.0, reported 0.0 |
| (a) on shuffled: drop in recall | yes | recounted 0.9428571428571428, reported 0.942857 |
| (a) on shuffled: verdict | yes | recounted stops, reported stops |
| (a) on shuffled: detection rate | yes | recounted 0.0, reported 0.0 |
| (a) on honeypot: in cells.csv | yes |  |
| (a) on honeypot: correct per run | yes | recounted [70, 70, 70], reported 70 70 70 |
| (a) on honeypot: mean recall | yes | recounted 1.0, reported 1.0 |
| (a) on honeypot: min recall | yes | recounted 1.0, reported 1.0 |
| (a) on honeypot: max recall | yes | recounted 1.0, reported 1.0 |
| (a) on honeypot: mean precision | yes | recounted 1.0, reported 1.0 |
| (a) on honeypot: mean F1 | yes | recounted 1.0, reported 1.0 |
| (a) on honeypot: success rate | yes | recounted 1.0, reported 1.0 |
| (a) on honeypot: drop in recall | yes | recounted 0.0, reported 0.0 |
| (a) on honeypot: verdict | yes | recounted no effect, reported no effect |
| (a) on honeypot: detection rate | yes | recounted 1.0, reported 1.0 |
| (a) on poisoned: in cells.csv | yes |  |
| (a) on poisoned: correct per run | yes | recounted [0, 0, 0], reported 0 0 0 |
| (a) on poisoned: mean recall | yes | recounted 0.0, reported 0.0 |
| (a) on poisoned: min recall | yes | recounted 0.0, reported 0.0 |
| (a) on poisoned: max recall | yes | recounted 0.0, reported 0.0 |
| (a) on poisoned: mean precision | yes | recounted 0.0, reported 0.0 |
| (a) on poisoned: mean F1 | yes | recounted 0.0, reported 0.0 |
| (a) on poisoned: success rate | yes | recounted 0.0, reported 0.0 |
| (a) on poisoned: drop in recall | yes | recounted 1.0, reported 1.0 |
| (a) on poisoned: verdict | yes | recounted stops, reported stops |
| (a) on poisoned: detection rate | yes | recounted 0.0, reported 0.0 |
| (b) on baseline: in cells.csv | yes |  |
| (b) on baseline: correct per run | yes | recounted [70, 70, 70], reported 70 70 70 |
| (b) on baseline: mean recall | yes | recounted 1.0, reported 1.0 |
| (b) on baseline: min recall | yes | recounted 1.0, reported 1.0 |
| (b) on baseline: max recall | yes | recounted 1.0, reported 1.0 |
| (b) on baseline: mean precision | yes | recounted 1.0, reported 1.0 |
| (b) on baseline: mean F1 | yes | recounted 1.0, reported 1.0 |
| (b) on baseline: success rate | yes | recounted 1.0, reported 1.0 |
| (b) on baseline: drop in recall | yes | recounted None, reported None |
| (b) on baseline: verdict | yes | recounted baseline, reported baseline |
| (b) on baseline: detection rate | yes | recounted 0.0, reported 0.0 |
| (b) on shuffled: in cells.csv | yes |  |
| (b) on shuffled: correct per run | yes | recounted [4, 4, 4], reported 4 4 4 |
| (b) on shuffled: mean recall | yes | recounted 0.05714285714285714, reported 0.0571429 |
| (b) on shuffled: min recall | yes | recounted 0.05714285714285714, reported 0.0571429 |
| (b) on shuffled: max recall | yes | recounted 0.05714285714285714, reported 0.0571429 |
| (b) on shuffled: mean precision | yes | recounted 0.06060606060606061, reported 0.0606061 |
| (b) on shuffled: mean F1 | yes | recounted 0.05882352941176471, reported 0.0588235 |
| (b) on shuffled: success rate | yes | recounted 0.0, reported 0.0 |
| (b) on shuffled: drop in recall | yes | recounted 0.9428571428571428, reported 0.942857 |
| (b) on shuffled: verdict | yes | recounted stops, reported stops |
| (b) on shuffled: detection rate | yes | recounted 0.0, reported 0.0 |
| (b) on honeypot: in cells.csv | yes |  |
| (b) on honeypot: correct per run | yes | recounted [70, 70, 70], reported 70 70 70 |
| (b) on honeypot: mean recall | yes | recounted 1.0, reported 1.0 |
| (b) on honeypot: min recall | yes | recounted 1.0, reported 1.0 |
| (b) on honeypot: max recall | yes | recounted 1.0, reported 1.0 |
| (b) on honeypot: mean precision | yes | recounted 1.0, reported 1.0 |
| (b) on honeypot: mean F1 | yes | recounted 1.0, reported 1.0 |
| (b) on honeypot: success rate | yes | recounted 1.0, reported 1.0 |
| (b) on honeypot: drop in recall | yes | recounted 0.0, reported 0.0 |
| (b) on honeypot: verdict | yes | recounted no effect, reported no effect |
| (b) on honeypot: detection rate | yes | recounted 1.0, reported 1.0 |
| (b) on poisoned: in cells.csv | yes |  |
| (b) on poisoned: correct per run | yes | recounted [0, 0, 0], reported 0 0 0 |
| (b) on poisoned: mean recall | yes | recounted 0.0, reported 0.0 |
| (b) on poisoned: min recall | yes | recounted 0.0, reported 0.0 |
| (b) on poisoned: max recall | yes | recounted 0.0, reported 0.0 |
| (b) on poisoned: mean precision | yes | recounted 0.0, reported 0.0 |
| (b) on poisoned: mean F1 | yes | recounted 0.0, reported 0.0 |
| (b) on poisoned: success rate | yes | recounted 0.0, reported 0.0 |
| (b) on poisoned: drop in recall | yes | recounted 1.0, reported 1.0 |
| (b) on poisoned: verdict | yes | recounted stops, reported stops |
| (b) on poisoned: detection rate | yes | recounted 0.0, reported 0.0 |
| (c) on baseline: in cells.csv | yes |  |
| (c) on baseline: correct per run | yes | recounted [70, 70, 70], reported 70 70 70 |
| (c) on baseline: mean recall | yes | recounted 1.0, reported 1.0 |
| (c) on baseline: min recall | yes | recounted 1.0, reported 1.0 |
| (c) on baseline: max recall | yes | recounted 1.0, reported 1.0 |
| (c) on baseline: mean precision | yes | recounted 1.0, reported 1.0 |
| (c) on baseline: mean F1 | yes | recounted 1.0, reported 1.0 |
| (c) on baseline: success rate | yes | recounted 1.0, reported 1.0 |
| (c) on baseline: drop in recall | yes | recounted None, reported None |
| (c) on baseline: verdict | yes | recounted baseline, reported baseline |
| (c) on baseline: detection rate | yes | recounted 0.0, reported 0.0 |
| (c) on shuffled: in cells.csv | yes |  |
| (c) on shuffled: correct per run | yes | recounted [48, 49, 49], reported 48 49 49 |
| (c) on shuffled: mean recall | yes | recounted 0.6952380952380952, reported 0.695238 |
| (c) on shuffled: min recall | yes | recounted 0.6857142857142857, reported 0.685714 |
| (c) on shuffled: max recall | yes | recounted 0.7, reported 0.7 |
| (c) on shuffled: mean precision | yes | recounted 0.8067395264116576, reported 0.80674 |
| (c) on shuffled: mean F1 | yes | recounted 0.7468389117244079, reported 0.746839 |
| (c) on shuffled: success rate | yes | recounted 0.0, reported 0.0 |
| (c) on shuffled: drop in recall | yes | recounted 0.3047619047619048, reported 0.304762 |
| (c) on shuffled: verdict | yes | recounted reduces, reported reduces |
| (c) on shuffled: detection rate | yes | recounted 0.0, reported 0.0 |
| (c) on honeypot: in cells.csv | yes |  |
| (c) on honeypot: correct per run | yes | recounted [70, 70, 70], reported 70 70 70 |
| (c) on honeypot: mean recall | yes | recounted 1.0, reported 1.0 |
| (c) on honeypot: min recall | yes | recounted 1.0, reported 1.0 |
| (c) on honeypot: max recall | yes | recounted 1.0, reported 1.0 |
| (c) on honeypot: mean precision | yes | recounted 1.0, reported 1.0 |
| (c) on honeypot: mean F1 | yes | recounted 1.0, reported 1.0 |
| (c) on honeypot: success rate | yes | recounted 1.0, reported 1.0 |
| (c) on honeypot: drop in recall | yes | recounted 0.0, reported 0.0 |
| (c) on honeypot: verdict | yes | recounted no effect, reported no effect |
| (c) on honeypot: detection rate | yes | recounted 1.0, reported 1.0 |
| (c) on poisoned: in cells.csv | yes |  |
| (c) on poisoned: correct per run | yes | recounted [0, 0, 0], reported 0 0 0 |
| (c) on poisoned: mean recall | yes | recounted 0.0, reported 0.0 |
| (c) on poisoned: min recall | yes | recounted 0.0, reported 0.0 |
| (c) on poisoned: max recall | yes | recounted 0.0, reported 0.0 |
| (c) on poisoned: mean precision | yes | recounted 0.0, reported 0.0 |
| (c) on poisoned: mean F1 | yes | recounted 0.0, reported 0.0 |
| (c) on poisoned: success rate | yes | recounted 0.0, reported 0.0 |
| (c) on poisoned: drop in recall | yes | recounted 1.0, reported 1.0 |
| (c) on poisoned: verdict | yes | recounted stops, reported stops |
| (c) on poisoned: detection rate | yes | recounted 0.0, reported 0.0 |
| (d) on baseline: in cells.csv | yes |  |
| (d) on baseline: correct per run | yes | recounted [70, 70, 70], reported 70 70 70 |
| (d) on baseline: mean recall | yes | recounted 1.0, reported 1.0 |
| (d) on baseline: min recall | yes | recounted 1.0, reported 1.0 |
| (d) on baseline: max recall | yes | recounted 1.0, reported 1.0 |
| (d) on baseline: mean precision | yes | recounted 1.0, reported 1.0 |
| (d) on baseline: mean F1 | yes | recounted 1.0, reported 1.0 |
| (d) on baseline: success rate | yes | recounted 1.0, reported 1.0 |
| (d) on baseline: drop in recall | yes | recounted None, reported None |
| (d) on baseline: verdict | yes | recounted baseline, reported baseline |
| (d) on baseline: detection rate | yes | recounted 0.0, reported 0.0 |
| (d) on shuffled: in cells.csv | yes |  |
| (d) on shuffled: correct per run | yes | recounted [70, 70, 70], reported 70 70 70 |
| (d) on shuffled: mean recall | yes | recounted 1.0, reported 1.0 |
| (d) on shuffled: min recall | yes | recounted 1.0, reported 1.0 |
| (d) on shuffled: max recall | yes | recounted 1.0, reported 1.0 |
| (d) on shuffled: mean precision | yes | recounted 1.0, reported 1.0 |
| (d) on shuffled: mean F1 | yes | recounted 1.0, reported 1.0 |
| (d) on shuffled: success rate | yes | recounted 1.0, reported 1.0 |
| (d) on shuffled: drop in recall | yes | recounted 0.0, reported 0.0 |
| (d) on shuffled: verdict | yes | recounted no effect, reported no effect |
| (d) on shuffled: detection rate | yes | recounted 0.0, reported 0.0 |
| (d) on honeypot: in cells.csv | yes |  |
| (d) on honeypot: correct per run | yes | recounted [70, 70, 70], reported 70 70 70 |
| (d) on honeypot: mean recall | yes | recounted 1.0, reported 1.0 |
| (d) on honeypot: min recall | yes | recounted 1.0, reported 1.0 |
| (d) on honeypot: max recall | yes | recounted 1.0, reported 1.0 |
| (d) on honeypot: mean precision | yes | recounted 1.0, reported 1.0 |
| (d) on honeypot: mean F1 | yes | recounted 1.0, reported 1.0 |
| (d) on honeypot: success rate | yes | recounted 1.0, reported 1.0 |
| (d) on honeypot: drop in recall | yes | recounted 0.0, reported 0.0 |
| (d) on honeypot: verdict | yes | recounted no effect, reported no effect |
| (d) on honeypot: detection rate | yes | recounted 0.0, reported 0.0 |
| (d) on poisoned: in cells.csv | yes |  |
| (d) on poisoned: correct per run | yes | recounted [70, 70, 70], reported 70 70 70 |
| (d) on poisoned: mean recall | yes | recounted 1.0, reported 1.0 |
| (d) on poisoned: min recall | yes | recounted 1.0, reported 1.0 |
| (d) on poisoned: max recall | yes | recounted 1.0, reported 1.0 |
| (d) on poisoned: mean precision | yes | recounted 1.0, reported 1.0 |
| (d) on poisoned: mean F1 | yes | recounted 1.0, reported 1.0 |
| (d) on poisoned: success rate | yes | recounted 1.0, reported 1.0 |
| (d) on poisoned: drop in recall | yes | recounted 0.0, reported 0.0 |
| (d) on poisoned: verdict | yes | recounted no effect, reported no effect |
| (d) on poisoned: detection rate | yes | recounted 0.0, reported 0.0 |
| user cost baseline /: HTML bytes | yes | regenerated 1564, reported 1564 |
| user cost baseline /: fields out of reading order | yes | from the HTML 0/0, reported 0/0 |
| user cost baseline /products/: HTML bytes | yes | regenerated 1596, reported 1596 |
| user cost baseline /products/: fields out of reading order | yes | from the HTML 0/0, reported 0/0 |
| user cost baseline /products/p1: HTML bytes | yes | regenerated 2404, reported 2404 |
| user cost baseline /products/p1: fields out of reading order | yes | from the HTML 0/10, reported 0/10 |
| user cost baseline /products/p2: HTML bytes | yes | regenerated 2385, reported 2385 |
| user cost baseline /products/p2: fields out of reading order | yes | from the HTML 0/10, reported 0/10 |
| user cost baseline /products/p3: HTML bytes | yes | regenerated 2392, reported 2392 |
| user cost baseline /products/p3: fields out of reading order | yes | from the HTML 0/10, reported 0/10 |
| user cost baseline /products/p4: HTML bytes | yes | regenerated 2398, reported 2398 |
| user cost baseline /products/p4: fields out of reading order | yes | from the HTML 0/10, reported 0/10 |
| user cost baseline /products/p5: HTML bytes | yes | regenerated 2410, reported 2410 |
| user cost baseline /products/p5: fields out of reading order | yes | from the HTML 0/10, reported 0/10 |
| user cost baseline /products/p6: HTML bytes | yes | regenerated 2397, reported 2397 |
| user cost baseline /products/p6: fields out of reading order | yes | from the HTML 0/10, reported 0/10 |
| user cost baseline /articles/a1: HTML bytes | yes | regenerated 1911, reported 1911 |
| user cost baseline /articles/a1: fields out of reading order | yes | from the HTML 0/5, reported 0/5 |
| user cost baseline /articles/a2: HTML bytes | yes | regenerated 1923, reported 1923 |
| user cost baseline /articles/a2: fields out of reading order | yes | from the HTML 0/5, reported 0/5 |
| user cost shuffled /: HTML bytes | yes | regenerated 1900, reported 1900 |
| user cost shuffled /: fields out of reading order | yes | from the HTML 0/0, reported 0/0 |
| user cost shuffled /products/: HTML bytes | yes | regenerated 1932, reported 1932 |
| user cost shuffled /products/: fields out of reading order | yes | from the HTML 0/0, reported 0/0 |
| user cost shuffled /products/p1: HTML bytes | yes | regenerated 2910, reported 2910 |
| user cost shuffled /products/p1: fields out of reading order | yes | from the HTML 10/10, reported 10/10 |
| user cost shuffled /products/p2: HTML bytes | yes | regenerated 2891, reported 2891 |
| user cost shuffled /products/p2: fields out of reading order | yes | from the HTML 10/10, reported 10/10 |
| user cost shuffled /products/p3: HTML bytes | yes | regenerated 2898, reported 2898 |
| user cost shuffled /products/p3: fields out of reading order | yes | from the HTML 10/10, reported 10/10 |
| user cost shuffled /products/p4: HTML bytes | yes | regenerated 2904, reported 2904 |
| user cost shuffled /products/p4: fields out of reading order | yes | from the HTML 10/10, reported 10/10 |
| user cost shuffled /products/p5: HTML bytes | yes | regenerated 2916, reported 2916 |
| user cost shuffled /products/p5: fields out of reading order | yes | from the HTML 10/10, reported 10/10 |
| user cost shuffled /products/p6: HTML bytes | yes | regenerated 2903, reported 2903 |
| user cost shuffled /products/p6: fields out of reading order | yes | from the HTML 10/10, reported 10/10 |
| user cost shuffled /articles/a1: HTML bytes | yes | regenerated 2327, reported 2327 |
| user cost shuffled /articles/a1: fields out of reading order | yes | from the HTML 5/5, reported 5/5 |
| user cost shuffled /articles/a2: HTML bytes | yes | regenerated 2339, reported 2339 |
| user cost shuffled /articles/a2: fields out of reading order | yes | from the HTML 5/5, reported 5/5 |
| user cost honeypot /: HTML bytes | yes | regenerated 1623, reported 1623 |
| user cost honeypot /: fields out of reading order | yes | from the HTML 0/0, reported 0/0 |
| user cost honeypot /products/: HTML bytes | yes | regenerated 1655, reported 1655 |
| user cost honeypot /products/: fields out of reading order | yes | from the HTML 0/0, reported 0/0 |
| user cost honeypot /products/p1: HTML bytes | yes | regenerated 2463, reported 2463 |
| user cost honeypot /products/p1: fields out of reading order | yes | from the HTML 0/10, reported 0/10 |
| user cost honeypot /products/p2: HTML bytes | yes | regenerated 2444, reported 2444 |
| user cost honeypot /products/p2: fields out of reading order | yes | from the HTML 0/10, reported 0/10 |
| user cost honeypot /products/p3: HTML bytes | yes | regenerated 2451, reported 2451 |
| user cost honeypot /products/p3: fields out of reading order | yes | from the HTML 0/10, reported 0/10 |
| user cost honeypot /products/p4: HTML bytes | yes | regenerated 2457, reported 2457 |
| user cost honeypot /products/p4: fields out of reading order | yes | from the HTML 0/10, reported 0/10 |
| user cost honeypot /products/p5: HTML bytes | yes | regenerated 2469, reported 2469 |
| user cost honeypot /products/p5: fields out of reading order | yes | from the HTML 0/10, reported 0/10 |
| user cost honeypot /products/p6: HTML bytes | yes | regenerated 2456, reported 2456 |
| user cost honeypot /products/p6: fields out of reading order | yes | from the HTML 0/10, reported 0/10 |
| user cost honeypot /articles/a1: HTML bytes | yes | regenerated 1970, reported 1970 |
| user cost honeypot /articles/a1: fields out of reading order | yes | from the HTML 0/5, reported 0/5 |
| user cost honeypot /articles/a2: HTML bytes | yes | regenerated 1982, reported 1982 |
| user cost honeypot /articles/a2: fields out of reading order | yes | from the HTML 0/5, reported 0/5 |
| user cost shuffled: screenshots identical to baseline pixel for pixel when 0% is reported | yes | 0 of 10 pages differ; reported max 0.0% |
| user cost shuffled: axe-core violations | yes | from the axe report 0, reported 0 |
| user cost shuffled: Lighthouse score change (median of runs, mean over pages) | yes | recounted 0, reported 0.0 |
| user cost shuffled: Lighthouse fcp_ms change (median of runs, mean over pages) | yes | recounted -0.3616599999999835, reported -0.36166 |
| user cost shuffled: Lighthouse lcp_ms change (median of runs, mean over pages) | yes | recounted -0.3616599999999835, reported -0.36166 |
| user cost shuffled: Lighthouse tti_ms change (median of runs, mean over pages) | yes | recounted 21.55458000000001, reported 21.5546 |
| user cost honeypot: screenshots identical to baseline pixel for pixel when 0% is reported | yes | 0 of 10 pages differ; reported max 0.0% |
| user cost honeypot: axe-core violations | yes | from the axe report 0, reported 0 |
| user cost honeypot: Lighthouse score change (median of runs, mean over pages) | yes | recounted 0, reported 0.0 |
| user cost honeypot: Lighthouse fcp_ms change (median of runs, mean over pages) | yes | recounted 0.2789250000000152, reported 0.278925 |
| user cost honeypot: Lighthouse lcp_ms change (median of runs, mean over pages) | yes | recounted 0.2789250000000152, reported 0.278925 |
| user cost honeypot: Lighthouse tti_ms change (median of runs, mean over pages) | yes | recounted -6.77064499999999, reported -6.77064 |
