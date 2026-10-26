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

*Last updated: Mon Oct 26 (Turn 11 of the chat-keeper).*

> **▶ Resume here: Tue Oct 27.** Milestone 1 steps 1–5 are done. Next:
> 1. Set up the project on the laptop.
> 2. Step 6: Joseph writes the Test 2 fixture by hand.
> 3. Start scraper (a).
>
> The scoring script (Claude) starts once the fixture is in the repo.

---

## Milestone 1 · Oct 21 – Nov 3 · Test site and baseline scoring

⭐ **Done when:** the scoring script passes the hand-calculated Test 2, **and** scraper (a) scores at least 90% on baseline in each of 3 runs.

| Day | Tasks | Who |
|---|---|---|
| **Mon Oct 26** | ✅ Step 1: data list approved; tags scored as a set; p6 date kept. ✅ Steps 2–4: setup files, generator, server, 7 tests. ✅ `requests` and `beautifulsoup4` pinned. | J, C |
| | ✅ Site reviewed and approved (page structure, log fields, trap handling). | J |
| | ✅ Step 5: scraper output format and matching rules proposed and approved ([`docs/scraper-output.md`](docs/scraper-output.md)). | C, J |
| **Tue Oct 27** | Set up the project on the laptop (README: Setup and Usage). Clone the branch, run `npm ci` and `npm test` (expect 7 passing), then create a Python venv and run `pip install -r requirements.txt`. Moved from Mon Oct 26. | J |
| | Step 6: write the Test 2 fixture by hand, in the approved format (63 correct, 4 wrong, 3 missing → 0.90 and 2/70). | J |
| | Start scraper (a): Python environment, fetch one page with `requests`, find the label rows with BeautifulSoup. | J |
| **Wed Oct 28** | Step 7: scoring script and tests, from the midterm's prompt. Starts only after the fixture exists. | C |
| | Scraper (a): crawl loop (queue and visited set), page cap, `robots.txt` setting, `run=<id>` in the User-Agent. | J |
| **Thu Oct 29** | Step 8: verify the scoring script: run the tests, explain the diff line by line, break it on purpose. ⭐ **Check 1** | J |
| | Scraper (a): label-plus-next-text extraction; write output in the agreed format. | J |
| **Fri Oct 30** | Scraper (a): record 404s and timeouts and keep going. First full run on baseline; score it; fix problems. | J |
| **Sat Oct 31** | Buffer: finish (a) if behind. | J |
| **Sun Nov 1** | Step 10: baseline check. Run (a) 3 times with unique run IDs, score each run, and hand-count a few fields from one real run (§7 verification step 5). ⭐ **Check 2** | J |
| **Mon Nov 2** | Buffer and fixes. Record both checks in the chat-keeper; tick the README roadmap. | J, C |
| **Tue Nov 3** | **Milestone 1 closes.** Get the work onto `main` (pull request or upload). Read the Playwright for Python intro ahead of scraper (b). | J |

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
| **Wed Nov 4** | Pin Playwright in `requirements.txt` and install Chromium. | C |
| | Study a small Playwright example; start (b): load a page and read the rendered text right after the load event. | J |
| **Thu Nov 5** | (b): crawl loop that follows every link, hidden ones included; run ID in Playwright's User-Agent. | J |
| **Fri Nov 6** | (b): extraction and output. First baseline run; score it. | J |
| **Sat Nov 7** | Generator: per-page seeds saved with the output, and a slot where defenses plug in (§5: the generator saves the seeds). | C |
| | Start DOM shuffling: seeded shuffle of label and value elements in the source. | J |
| **Sun Nov 8** | Shuffling: restore the on-screen order with CSS `order`; the same seed must give byte-identical pages. | J |
| **Mon Nov 9** | Basic pixel-diff script (pixelmatch on Playwright screenshots). | C |
| | Finish shuffling. | J |
| **Tue Nov 10** | Test 4: source order differs, byte-identical regeneration, pixel diff ≤ 1%, all 10 screenshot pairs checked by eye. | J + C |
| | Start the honeypot link: one `display:none` link per page to the trap path. | J |
| **Wed Nov 11** | Finish the honeypot condition. Test 6: trap hit logged for run R, a normal page not flagged, missing User-Agent logged as `unknown`. | J + C |
| **Thu Nov 12** | Test 3 fixtures: work out the expected JSON by hand for a baseline page and for a page in a known scrambled order. | J |
| | Draft the harness that runs (a) and (b) on those fixtures. | C |
| **Fri Nov 13** | Run Test 3 for (a) and (b) on baseline and shuffled; fix problems. | J |
| **Sat Nov 14** | (b) baseline check: 3 runs at ≥ 90%. Test 1: baseline, shuffled and honeypot each have 10 pages and 70 fields; (a) and (b) reach ≥ 90% on baseline. | J |
| **Sun Nov 15** | Buffer. | — |
| **Mon Nov 16** | Buffer. Update the chat-keeper and README. | J, C |
| **Tue Nov 17** | ⚠️ **Cut-line 1.** Are (a), (b), shuffling and the honeypot all working? If not, no Ambitious work starts. | J |

---

## Milestone 3 · Nov 18 – Dec 1 · Essential experiment and user cost

⭐ **Done when** (§7):
- The results CSV has accuracy, honeypot hits and time per page for every cell, plus user-cost rows for each condition.
- Test 7 passes for the (a) and (b) crawl loops.

Thanksgiving week is light.

| Day | Tasks | Who |
|---|---|---|
| **Wed Nov 18** | Experiment runner: start the server on each condition, run each scraper 3 times with unique run IDs, save to a dated results folder. | C |
| | (A) Start poisoning: a same-format fake value for each field, real values in a per-page JSON file, a script that swaps them in after 2 s, and the fake-values file. | J |
| **Thu Nov 19** | Scoring script: honeypot hits and time per page from the request log; write the results CSV. | C |
| | (A) Continue poisoning. | J |
| **Fri Nov 20** | User-cost runner, part 1: screenshots after a 3 s wait, pixel diff against baseline, reading-order mismatch rate. | C |
| | (A) Test 5: no real value in the HTML; fakes shown at 0 s, real values at 3 s. | J + C |
| **Sat Nov 21** | User-cost runner, part 2: Lighthouse 5 times per page (median) and axe-core violations. | C |
| | (A) Start scraper (d): wait for 3 s with no DOM changes, with a 10 s timeout. | J |
| **Sun Nov 22** | (A) Scraper (d): skip hidden elements using computed styles, sort by computed CSS order. The (d) and poisoned-page parts of Test 3. | J |
| **Mon Nov 23** | **Essential runs:** (a) and (b) × baseline, shuffled and honeypot × 3 runs. Check the outputs. | J |
| **Tue Nov 24** | Test 7 for (a) and (b): a 404 link, a link cycle, a slow response, page cap 3. | J + C |
| | User-cost runs for each condition. | C |
| **Wed Nov 25** | (A) Set up (c) and (e): install Ollama; time 2–3 small models on 2–3 pages; record each model's name and digest. | C |
| | (A) Prompt, parsing and failure rules for (c) and (e). | J |
| **Thu Nov 26** | **Thanksgiving: off.** | — |
| **Fri Nov 27** | Light day or off. | — |
| **Sat Nov 28** | (A) Poisoned-site runs for (a), (b) and (d); (d) on baseline, shuffled and honeypot. | J |
| **Sun Nov 29** | (A) Baseline checks for (c) and (e): ≥ 90%, or reported as not usable. The stub-model parts of Test 7. | J + C |
| **Mon Nov 30** | Check that every Essential cell is in the results CSV and every condition has user-cost rows. | J |
| **Tue Dec 1** | ⚠️ **Cut-line 2.** Any Ambitious item that isn't running is dropped and reported as not done. | J |

---

## Milestone 4 · Dec 2 – Dec 10 · Final runs, analysis and packaging

⭐ **Done when** (§7): a clean rerun from the README reproduces the results table, the report PDF is final, and the submission commit is tagged by **Dec 8**.

| Day | Tasks | Who |
|---|---|---|
| **Wed Dec 2** | (A) Remaining Ambitious runs (Dec 2–5): (c) and (e), plus any remaining poisoning and (d) runs. **Tarpit:** only if all three other defenses and all five scrapers ran by Dec 1; if so, build it Dec 2–4. | J |
| **Thu Dec 3** | Script for the final tables: accuracy and fake-value rate by defense and scraper; honeypot hits and time per page; user cost against baseline. | C |
| | Check the tables against the raw outputs. Start the report. | J |
| **Fri Dec 4** | Figure pairing accuracy drop with user cost. Compare the results with the predicted pattern cell by cell and list every mismatch (§4). | J + C |
| **Sat Dec 5** | Final README and reproducibility manifest: OS, hardware, versions, model digests, config and seeds (§5). | C |
| | Report writing. | J |
| **Sun Dec 6** | Report writing. | J |
| **Mon Dec 7** | Clean rerun from the README on a fresh clone; confirm it reproduces the results table. Final report draft. | J + C |
| **Tue Dec 8** | Final report PDF. **Tag the submission commit.** | J |
| **Wed Dec 9** | Buffer. | — |
| **Thu Dec 10** | **Final submission deadline.** | J |
