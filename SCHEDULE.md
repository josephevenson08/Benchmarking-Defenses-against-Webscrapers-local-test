# Schedule

Day-by-day plan from **Mon Oct 26** to the **Dec 10** deadline. It is built from the midterm's milestone table (§7) and Gantt chart (Figure 3). Who does each task follows the midterm's AI-assistance split (§2, §7), which `CLAUDE.md` restates.

**Who**

| Code | Meaning |
|---|---|
| **J** | Joseph writes, runs or decides it. |
| **C** | Claude drafts it; Joseph reviews it. |
| **J + C** | Joseph works out expected results by hand; Claude drafts the code that checks them. |

**Markers**

| Marker | Meaning |
|---|---|
| ⭐ | A milestone completion check. |
| ⚠️ | A cut-line (decision point). |
| (A) | Ambitious work. Only happens if the Nov 17 cut-line passes. |
| ✅ | Done. |

*Last updated: Wed Nov 18 (Turn 293 of the chat-keeper): scraper (c) ran on all three conditions, ten days early (D88). Turn 289: (c) passed its baseline check four days early (D84). Earlier: Mon Nov 16 (Turn 250), Milestones 3 and 4 checked against the scrum feedback and decisions D66–D71, with time limits and fallbacks added.*

> **▶ Resume here (Mon Nov 16 evening):** the plan follows the scrum feedback: (c) first, then (d) (D66, D67); metrics comparable with published work (D68, D70, D71; `docs/metrics-plan.md`). The related-work table is already drafted from the papers.
> - **Tue Nov 17, first:** Joseph installs Ollama, sends his RAM, pulls 2–3 small models. Claude drafts the model-timing script.
> - **Time limits:** (c) gets until Sun Nov 22 to pass its baseline check, otherwise it is reported as "not usable" and work moves to (d). (d) gets until Sat Nov 28. The Essential work (runner, CSV, user cost, Essential runs, Test 7) is never delayed for (c) or (d).
> - Poisoning, (e) and the tarpit start only if (c) and (d) finish early. Otherwise Cut-line 2 (Dec 1) drops them and the report says so.

---

## Milestone 1 · Oct 21 – Nov 3 · Test site and baseline scoring

⭐ **Done when:** the scoring script passes the hand-calculated Test 2, **and** scraper (a) scores at least 90% on baseline in each of 3 runs.

| Day | Tasks | Who |
|---|---|---|
| **Mon Oct 26** | ✅ Step 1: data list approved; tags scored as a set; p6 date kept. ✅ Steps 2–4: setup files, generator, server, 7 tests. ✅ `requests` and `beautifulsoup4` pinned. | J, C |
| | ✅ Site reviewed and approved (page structure, log fields, trap handling). | J |
| | ✅ Step 5: scraper output format and matching rules proposed and approved ([`docs/scraper-output.md`](docs/scraper-output.md)). | C, J |
| **Tue Oct 27** | ✅ Set up the project on the laptop (README: Setup and Usage). Clone the branch, run `npm ci` and `npm test` (expect 7 passing), then create a Python venv and run `pip install -r requirements.txt`. Moved from Mon Oct 26. | J |
| | ✅ Step 6: Test 2 fixture (Joseph's design; files assembled by Claude at his request, D39) and Joseph's hand-calculated `expected.md`. | J |
| | ✅ Step 7 (a day early): scoring script and 24 tests reproduce 0.90 and 2/70 (pull request #4, D42). | C |
| | ✅ Step 8: Joseph verified the scoring script on his laptop: tests run, code read and explained, two deliberate breaks caught, clean rerun. **⭐ Check 1 passed** (two days early). | J |
| | ~~Start scraper (a)~~: not started; moved to Fri Oct 30 (re-planned in Turn 50, D44). | J |
| **Wed Oct 28** | ~~Scraper (a): crawl loop~~: moved to Fri Oct 30. | — |
| **Thu Oct 29** | ~~Scraper (a): extraction and output~~: moved to Sat Oct 31. | — |
| **Fri Oct 30** | Decide C20 (#1 page mapping, #6 tags as a list): 1 minute. | J |
| | ✅ **Step 9, scraper (a), part 1:** fetches `/products/p1` with a `run=` User-Agent, finds each label by its text, and prints all 10 correct label/value pairs (Joseph's code, Fri Oct 30). | J |
| | ✅ **Part 2a:** crawl loop from the home page (queue and visited set), following every link, same-site only, page cap 15. It visits all 10 pages (status 200), and every request is logged with the run ID (Joseph's code, Fri Oct 30). | J |
| | ✅ **Part 2b:** the inputs `--start-url --page-cap --robots --run-id --out` (`argparse`); `robots.txt` read with `RobotFileParser`. Obey skips disallowed pages and ignore doesn't (checked with a temporary `robots.txt`: 8 vs 10 pages); the page cap works; a missing `--run-id`/`--out` is an error (Joseph's code, Fri Oct 30). | J |
| **Sat Oct 31** | ✅ **Part 3 (done Fri, a day early):** the label-plus-next-text rule on every page using `data/fields.json`; output JSON in the approved format. Scored by `score.py`: **70/70 = 1.000** on baseline (Joseph's code, run in Claude's check). | J |
| | ✅ **Part 4 (done Fri, a day early):** `try`/`except` records `timeout` and `connection_error` and keeps going; a 404 is recorded by its status; a failed `robots.txt` download falls back to allowing every page. Tested on the laptop: normal, 404 and connection error (Joseph's code). Timing moved into part 3 (D45). | J |
| **Sun Nov 1** | **First full run** on baseline: already 70/70 in Claude's check on Fri. Joseph to confirm on the laptop (`results\dev\`). | J |
| **Fri Oct 30** | ✅ **Step 10, baseline check (moved up from Mon Nov 2):** 3 runs on Joseph's laptop, `a-baseline-1..3`, each **70/70 = 1.000** (0.016–0.020 s per page), saved in `results/2026-10-30-check2/` (D48). ⭐ **Check 2 passed.** Hand count of 5 fields: all correct (`results/2026-10-30-check2/hand-count.md`, §7 verification step 5). | J |
| | ✅ Check 2 recorded (D49), README roadmap ticked; closing pull request. | C |
| **Mon Nov 2** | Free: Milestone 1 finished early. | — |
| **Tue Nov 3** | **Milestone 1 deadline:** already met on Oct 30. | — |

---

## Milestone 2 · Nov 4 – Nov 17 · Scraper (b), shuffling, honeypot

⭐ **Done when** (§7):
- Tests 1, 4 and 6 pass.
- Test 3 passes for (a) and (b) on the baseline and shuffled fixtures.
- (b) scores at least 90% on baseline in 3 runs.
- Shuffled pages differ from baseline by no more than 1% of pixels.
- A trap request is logged with its run ID.

| Day | Tasks | Who |
|---|---|---|
| **Wed Nov 4** | ✅ Pin Playwright in `requirements.txt` (1.63.0, D50) and add the Chromium install step. | C |
| | ✅ Ran two Playwright examples on the laptop. (b)'s design chosen (D51). Wrote `scrapers/b_browser_text.py` part 1: Chromium loads `/products/p1`, takes `page.content()` after the load event, and applies (a)'s field loop and ran it on the laptop: status 200, all 10 values correct, logged as `b-test-1`. Commit pending. | J |
| **Thu Nov 5** | ✅ (b): crawl loop that follows every link, hidden ones included; run ID in Playwright's User-Agent. Ran on the laptop as `b-test-3`: 10 pages in (a)'s order, 70 records found, 11 log lines (robots.txt + 10 pages). Committed (`3b96a5a`). | J |
| **Fri Nov 6** | ✅ (b): extraction and output. First baseline run; score it. `b-baseline-1`: 70/70 = 1.000, 0.356 s, 0.036 s per page ((a): 0.016–0.020 s). Clock times the crawl only (D52). Committed (`6d3fee9`). | J |
| **Sat Nov 7** | ✅ Generator: per-page seeds saved with the output, and a slot where defenses plug in (§5: the generator saves the seeds). One file per defense in `site/defenses/` (`style`, `fieldRows(rows, rng)`); seeds in the manifest; baseline pages unchanged byte for byte; 14 tests pass. | C |
| | ✅ Start DOM shuffling: seeded shuffle of label and value elements in the source. `site/defenses/shuffled.js` part 1: all labels and values of a page mixed in one `.fields` block (D54), each carrying its on-screen position as `style="order: N"`; p1 matches the expected order. Preview: scraper (a) scores 4/70 on it (Claude's check, not a recorded run). Commit pending. | J |
| **Sun Nov 8** | ✅ (done early, Sat Nov 7) Shuffling: restore the on-screen order with CSS `order`; the same seed must give byte-identical pages. Joseph's `style`: `.fields` row + wrap, label 10rem (1rem gap as padding), value `calc(100% - 10rem)`, baseline padding and border. Claude's check: all 8 item pages pixel-identical to baseline at 1280 px and 375 px; regenerating gives identical files. Commit pending. | J |
| **Mon Nov 9** | ✅ Basic pixel-diff script (pixelmatch on Playwright screenshots). `measurement/screenshots.py` (Python Playwright, 1280×800, full page, 3 s wait) and `measurement/pixel_diff.mjs` (pixelmatch 7.2.0, pngjs 7.0.0). Shuffled vs baseline: 0.000% on all 10 pages; a broken layout reads up to 58%. | C |
| | ✅ Finish shuffling. Comments and tidy-up in `site/defenses/shuffled.js`; pixel-diff on the laptop: shuffled vs baseline 0.000% on all 10 pages. Committed (`eef2fdf`). | J |
| **Tue Nov 10** | ✅ Test 4: source order differs, byte-identical regeneration, pixel diff ≤ 1%, all 10 screenshot pairs checked by eye. ⭐ **Passed** on the laptop (12 files identical; 8/8 item pages reordered; 0.000% on all 10 pages; 10/10 "yes" by eye), saved in `results/2026-11-10-test4/`. Claude: `measurement/test4.py` and the generator's `mainEnd` hook for the honeypot. | J + C |
| | ✅ Start the honeypot link: one `display:none` link per page to the trap path. `site/defenses/honeypot.js`: `mainEnd` returns `<a href="/trap" style="display: none;">Archive</a>` at the end of every page's `<main>`. Laptop practice run: scraper (a) as `a-honeypot-1` visited 11 pages including `/trap`, logged as `honeypot_hit: true`. Claude's check: 0.000% pixels vs baseline; (a) and (b) each one trap hit and 70/70. Committed (`ed19725`). | J |
| **Wed Nov 11** | ✅ (done early, Tue Nov 10) Finish the honeypot condition. Test 6: trap hit logged for run R, a normal page not flagged, missing User-Agent logged as `unknown`. ⭐ **Passed** on the laptop (`measurement/test6.py`): Test 6 PASS; honeypot pages PASS (10/10 one hidden trap link, 0.000% pixels). Saved in `results/2026-11-10-test6/` (`e72ea07`). | J + C |
| **Thu Nov 12** | ✅ (done early, Wed Nov 11) Test 3 fixtures: work out the expected JSON by hand for a baseline page and for a page in a known scrambled order. Joseph's `expected.json` for `baseline-p2` (10 real values) and `shuffled-p1` (9 records: the text after each label in source order; Brand, the last element, gives none). Committed (`4203f7f`). | J |
| | ✅ (done early, Tue Nov 10) Draft the harness that runs (a) and (b) on those fixtures. `measurement/test3.py`, with the two saved pages in `measurement/fixtures/test3/` (`baseline-p2`, `shuffled-p1`); the `expected.json` files are left empty for Joseph's hand-worked answers. | C |
| **Fri Nov 13** | ✅ (done early, Wed Nov 11) Run Test 3 for (a) and (b) on baseline and shuffled; fix problems. ⭐ **Passed** on the laptop: (a) and (b) match the hand-worked output exactly on both pages (10/10 and 9/9 records). Committed (`results/2026-11-11-test3/`). | J |
| **Sat Nov 14** | ✅ (done early, Wed Nov 11) (b) baseline check: 3 runs at ≥ 90%. Test 1: baseline, shuffled and honeypot each have 10 pages and 70 fields; (a) and (b) reach ≥ 90% on baseline. ⭐ **Passed** on the laptop (`measurement/test1.py`, commit `7c5ae6c`): all three conditions 10 pages / 70 fields; (a) and (b) 70/70 in all 3 runs each ((a) 0.015–0.017 s per page, (b) 0.026–0.031 s). Committed (`ff9bf29`, `results/2026-11-11-test1/`). | J |
| **Sun Nov 15** | Buffer. | — |
| **Mon Nov 16** | Buffer. Update the chat-keeper and README. | J, C |
| **Tue Nov 17** | ⚠️ **Cut-line 1.** Are (a), (b), shuffling and the honeypot all working? If not, no Ambitious work starts. | J |

---

## Milestone 3 · Nov 17 – Dec 1 · Essential experiment, user cost, then (c) and (d)

⭐ **Done when** (§7, unchanged), ✅ **met on Fri Nov 20** (D94):
- The results CSV has accuracy, honeypot hits and time per page for every cell, plus user-cost rows for each condition. ✅ `results/2026-11-20-results/` and `results/2026-11-20-user-cost-full/`.
- Test 7 passes for the (a) and (b) crawl loops. ✅ Laptop run, Fri Nov 20.

**Done when, for the Ambitious work as re-planned** (§1 items 3 and 4, narrowed by D66–D67):
- (c) passes its baseline check (3 runs at ≥ 90%) and runs 3 times on baseline, shuffled and honeypot, or is reported as "not usable".
- (d) passes the (d) part of Test 3 and runs 3 times on baseline, shuffled and honeypot.
- The defense-by-scraper table is filled in for (a)–(d), with the standard metrics from `docs/metrics-plan.md`.

Re-planned on Mon Nov 16 after the scrum meeting (D66–D71). The instructor asked for the LLM scraper (c) and the adaptive scraper (d) next, and for metrics that can be compared with published work. Joseph chose (c) first. Both scrapers are Joseph's code (§2); Claude explains, shows standalone examples, reviews, and drafts the tooling around them. The Essential tooling stays on its dates and is never delayed for (c) or (d). Thanksgiving week is light.

**Time limits:** (c) until Sun Nov 22 for its baseline check, otherwise "not usable" (§4 allows this for a model that cannot reach 90% on baseline) and work moves to (d). (d) until Sat Nov 28 for its runs. Whatever isn't running on Tue Dec 1 is dropped and reported (§7).

| Day | Tasks | Who |
|---|---|---|
| **Tue Nov 17** | ⚠️ **Cut-line 1** (Milestone 2's last day): (a), (b), shuffling and the honeypot all work. ✅ Already met on Nov 11. | J |
| | (A) Install Ollama on the laptop and pull 2–3 small models (CPU only: Intel Iris Xe; sizes chosen from the laptop's RAM). Check each model's license allows local research use (§2). Ollama 0.40.16 installed; `gemma3:1b` (806 MB) and `llama3.2:3b` (2.0 GB) pulled; 16 GB RAM, so `qwen3:4b` too. ✅ Joseph confirmed all three licenses allow local research use. | J |
| | ✅ Model-timing script: time each pulled model on the text of 2–3 pages; record each model's name and digest, and the prompt tokens per page (D71). `measurement/time_models.py`, 6 tests, checked end to end against a stand-in for Ollama. Joseph runs it on the laptop. | C |
| **Wed Nov 18** | ✅ Experiment runner: start the server on each condition, run each scraper 3 times with unique run IDs, save to a dated results folder. `measurement/run_experiment.py` (D76), 6 tests; checked on the full Essential grid in the cloud: 18/18 runs in 16 s, the same results as Tests 1, 4 and 6. | C |
| | (A) ✅ Scraper (c), part 1: get each page's rendered text with (b)'s crawler; a first standalone call to Ollama. `scrapers/c_llm_text.py` (a copy of (b)) prints each page's `inner_text`; a practice call to `llama3.2:3b` returned the right name, price, SKU and rating in 1.6–3 s. | J |
| **Thu Nov 19** | ✅ (one day late, Fri Nov 20) Scoring: honeypot hits and time per page from the request log; write the results CSV. Count page requests only (a browser may also fetch `/favicon.ico`, and defenses may add script or style files). `scoring/results.py` (D90), 10 tests: `results.csv` (one row per run), `cells.csv` (one per scraper and condition) and `summary.md`. Time per page stays the midterm's (crawl seconds ÷ pages fetched, from the output); the log gives page requests (checked against pages fetched), honeypot hits and server response time. ✅ Laptop run identical to the cloud's, committed as `results/2026-11-20-results/`. | C |
| | (A) ✅ (timed early, Tue Nov 17) Time the models with the script and choose one for (c); record its name and digest. 3 models timed on the laptop: `llama3.2:3b` 6.8 s/page, 50/50 values found; `gemma3:1b` 5.7 s/page, 48/50; `qwen3:4b` 36.7 s/page and hit the 400-token cap on every call (thinking-off was requested, but its replies still began with written-out reasoning). **Chosen: `llama3.2:3b`** (3.2B, Q4_K_M, digest `a80c4f17acd5`; D75). Results to commit: `results/2026-11-17-model-timing/`. | J |
| **Fri Nov 20** | ✅ Standard metrics in the scoring (D68, D70): field-level precision, recall and F1; extraction success rate (ESR, a run with 70/70 correct); relative reduction against baseline; honeypot detection and evasion rates. Accuracy and the fake-value rate stay as they are. In `scoring/results.py` (D90), with the midterm's verdict per cell. On the 27 Nov 18 runs it gives the same numbers as the Turn 304 preview. | C |
| | ✅ User-cost runner, part 1: screenshots after a 3 s wait, pixel diff and SSIM against baseline, reading-order mismatch rate, HTML size per page against baseline (D71). `measurement/user_cost.py` and SSIM in `measurement/pixel_diff.mjs` (D91); 13 new tests; SSIM matches scikit-image to 13 decimals. Cloud check: shuffled 0.000% pixels, SSIM 1.0000, reading order 70/70 fields out of order, HTML +21.2%; honeypot 0.000%, 1.0000, 0/70, +2.8%. ✅ Laptop run (commit `b3d1a05`, Windows) gives the same results, committed as `results/2026-11-20-user-cost/`. Joseph reviews the reading-order rule (§3, C38). | C |
| | (A) ✅ (done early, Wed Nov 18) Scraper (c), part 2: one fixed prompt per page type listing the field names, temperature 0; parse the reply as JSON. The page type comes from the URL (D78); JSON mode (D79); main content only (D80); the prompt asks for exact copies (D81). First scored run `c-test-4` on baseline: 70/70, 6.1 s per page (61 s per run). | J |
| **Sat Nov 21** | ✅ (done early, Fri Nov 20) User-cost runner, part 2: Lighthouse 5 times per page (median; performance score, FCP, LCP, TTI as changes from baseline) and axe-core violations. `measurement/lighthouse.mjs` and axe-core in `measurement/user_cost.py` (D92); Lighthouse 13.6.0 (defaults: mobile, simulated throttling), axe-core 4.14.0, chrome-launcher 1.2.3, pinned. Cloud check (1 Lighthouse run per page): axe-core 0 violations on every condition (and 8 caught on a deliberately broken test page); Lighthouse changes within ±3 ms and 0.1 points except one 1-run TTI outlier. Joseph runs `npm install` and the full run (5 runs per page) on the laptop. | C |
| | (A) ✅ (done early, Wed Nov 18) Scraper (c), part 3: require every expected key, convert price and rating to numbers; invalid JSON, a missing key or a timeout is a failure, with no retry. First baseline run. Failure rules D82, D83 (`model_timeout`, `invalid_json`, `missing_key`, `model_error`; each tested on the laptop); `c-test-5` 70/70 with price and rating as numbers. Commit `ba437ad`. | J |
| **Sun Nov 22** | (A) ✅ (done early, Wed Nov 18) Scraper (c) baseline check: 3 runs at ≥ 90%, or reported as not usable. **Time limit for (c).** ⭐ Passed (D84): `c-baseline-1/2/3` all 70/70 (1.000), 5.3–5.7 s per page, 54–58 s per run, commit `ba437ad`, model `llama3.2:3b`. Results folder `results/2026-11-18-c-baseline/` to commit. | J |
| | (A) Start scraper (d): wait until the page has had no changes for 3 s, with a 10 s timeout. | J |
| **Mon Nov 23** | ✅ (done early, Wed Nov 18) **Essential runs:** (a) and (b) × baseline, shuffled and honeypot × 3 runs, with the runner. Check the outputs. ⭐ 18/18 runs on the laptop (commit `defff7a`): (a) and (b) 70/70 on baseline, 4/70 on shuffled, 70/70 on honeypot with 11 pages (the trap). Results folder `results/2026-11-18-experiment/` to commit. | J |
| **Tue Nov 24** | ✅ (done early, Fri Nov 20) Test 7 for (a) and (b): a 404 link, a link cycle, a slow response, page cap 3. Harness built early (Fri Nov 20): `measurement/test7.py` (D93), 9 tests; cloud run passes for (a), (b) and (c) (24 s). ⭐ Laptop run passes for (a) and (b) (commit `86db946`). | J + C |
| | User-cost runs for each condition. | C |
| | (A) Scraper (d): skip elements that computed style hides (hidden links too); sort fields by computed CSS order, then the label-plus-next rule. | J |
| **Wed Nov 25** | (A) The (d) part of Test 3; (d) baseline check (3 runs at ≥ 90%). | J |
| | Related-work table (`docs/metrics-plan.md`): the published side is already drafted from the papers; fill in our column with the Essential results ((a) and (b)). | C drafts, J reviews |
| **Thu Nov 26** | **Thanksgiving: off.** | — |
| **Fri Nov 27** | Light day or off. | — |
| **Sat Nov 28** | (A) Runs: (c) (if usable) and (d) × baseline, shuffled and honeypot × 3 runs. **Time limit for (d).** ✅ (c) part done early (Wed Nov 18, D88): 9/9 runs, commit `8e361f3`: baseline 70/70 × 3; shuffled 48, 49, 49/70 (0.686–0.700: reduces, does not stop); honeypot 70/70 × 3 with 11 pages (the trap). Results folder `results/2026-11-18-c-all/` to commit. The first attempt (`results/2026-11-18-c-defended/`) crashed on the trap page and led to the fix in `8e361f3` (D86, D87). (d) still to run. | J |
| **Sun Nov 29** | (A) The stub-model parts of Test 7 for (c). | J + C |
| | Honeypot false-positive check: a human-like visitor that clicks only visible links should never hit the trap (D68). | C |
| **Mon Nov 30** | Check that every cell is in the results CSV with the standard metrics, and every condition has user-cost rows. | J |
| **Tue Dec 1** | ⚠️ **Cut-line 2.** Any Ambitious item that isn't running is dropped and reported as not done. Poisoning, (e) and the tarpit start only if (c) and (d) finished early. | J |

---

## Milestone 4 · Dec 2 – Dec 10 · Final runs, analysis and packaging

⭐ **Done when** (§7): a clean rerun from the README reproduces the results table, the report PDF is final, and the submission commit is tagged by **Dec 8**.

| Day | Tasks | Who |
|---|---|---|
| **Wed Dec 2** | (A) Remaining Ambitious runs (Dec 2–5): any remaining (c) and (d) runs; poisoning and (e) only if they were running by Dec 1. **Tarpit:** only if all three other defenses and all five scrapers ran by Dec 1; if so, build it Dec 2–4. | J |
| **Thu Dec 3** | Script for the final tables, with the standard metrics (`docs/metrics-plan.md`): accuracy (= recall), precision, F1, ESR, fake-value rate and relative reduction by defense and scraper; honeypot detection, evasion and false-positive rates and time per page; user cost against baseline (pixel diff, SSIM, Lighthouse changes, axe-core, reading order, HTML size). Fill our column of the related-work table with (c) and (d). | C |
| | Check the tables against the raw outputs. Start the report. | J |
| **Fri Dec 4** | Figure: protection (relative reduction) against user cost, one point per defense and scraper. Compare the results with the predicted pattern cell by cell and list every mismatch (§4); compare with the related-work table and note where we agree or differ with published findings. | J + C |
| **Sat Dec 5** | Final README and reproducibility manifest: OS, hardware, versions, model digests, config and seeds (§5). | C |
| | Report writing: results with the standard metrics, the related-work comparison, and a scope-change section (instructor feedback; D66–D69; what was not done and which hypothesis that leaves untested). | J |
| **Sun Dec 6** | Report writing. | J |
| **Mon Dec 7** | Clean rerun from the README on a fresh clone; confirm it reproduces the results table. Final report draft. | J + C |
| **Tue Dec 8** | Final report PDF. **Tag the submission commit.** | J |
| **Wed Dec 9** | Buffer. | — |
| **Thu Dec 10** | **Final submission deadline.** | J |
