# Metrics plan: making the results comparable with other work

Decisions D68 (chat-keeper, Turn 240), D69 (Turn 246), D70 (Turn 248) and D71 (Turn 249), after the Nov 16 scrum meeting. The instructor's point: a result such as "4/70" says little on its own. A reader can't tell whether it is good or bad, typical or unusual, until it is compared with something. This plan says what each number is compared with, and which published study uses the same measure.

Status: the published side of the related-work table is done (below, checked against the papers). Built: the model-timing script with token counts (Tue Nov 17, `measurement/time_models.py`) and the scoring changes (Fri Nov 20, `scoring/results.py`: precision, recall, F1, extraction success rate, relative reduction, verdict, honeypot detection and evasion rates) and the user-cost runner (Fri Nov 20, `measurement/user_cost.py`: pixel difference, SSIM, reading order, HTML size, axe-core, Lighthouse changes). Still planned: our side of the related-work table on Wed Nov 25 ((a), (b)) and Thu Dec 3 ((c), (d)); the honeypot false-positive check on Sun Nov 29 (`SCHEDULE.md`). The scraper output format and the matching rules (`docs/scraper-output.md`, D31–D35) do not change.

## Three layers of comparison

1. **Against our own baseline.** Every defended result is reported next to the same scraper on the undefended site, as a **relative reduction**. This is the most portable number: it cancels out how easy or hard our site is, so it can sit next to "before → after" results from other studies.
2. **Against standard definitions and yardsticks.** Every measure is also reported in the form other work uses (precision, recall, F1, success rate, detection and false-positive rates, SSIM, Lighthouse, WCAG/axe-core). Some of these come with published thresholds that give meaning without needing another paper.
3. **Against published results.** A related-work table puts our numbers next to published ones in the same units, and says how each study's setting differs from ours.

## The measures

| What we measure | Kept from the midterm (§4) | Standard form we add | Published study using it [ref] | Outside yardstick |
|---|---|---|---|---|
| Extraction quality, per field | Accuracy = correct ÷ 70 | Field-level **recall** (the same number as accuracy), **precision** = correct ÷ fields returned, **F1** | WebCloak [1]: scraping recall = \|extracted ∩ target\| ÷ \|target\| (exactly our accuracy) and scraping precision = correct ÷ extracted. FreeDOM [3] and the SWDE line of work: page-level F1 per field, one (top-1) value per field. | 1.0 = everything right |
| Extraction quality, per run | — | **Extraction success rate (ESR)** = share of runs whose output is complete and correct (here: 70/70) | Beyond BeautifulSoup [2]: ESR averaged over 3 trials per site | 1.0 = every run fully right |
| Defense effect | "Reduces" and "stops" rules (§4) | **Relative reduction** = 1 − score with the defense ÷ score without (0 = no effect, 1 = fully stopped), for recall and F1 | WebCloak [1]: recall before → after the defense | The size of the drop, not the absolute score |
| Fake values (poisoning, if built) | Fake-value rate = fakes ÷ 70 | Same | — | 0 = no fakes taken |
| Honeypot | Hits per run (request log) | **Detection rate** (true positive rate) = scraper runs caught ÷ scraper runs; **evasion rate** = 1 − detection rate; **false-positive rate** from a human-like visitor that clicks only visible links | Shy Guys [4]: TP/FN over bots, FP/TN over humans. FP-Inconsistent [5]: detection, evasion and true-negative rates | Catch most bots at a low false-positive rate |
| Speed for the scraper | Time per page | Same, plus slowdown against the fastest scraper | Beyond BeautifulSoup [2]: average execution time per successful run | Ratio, e.g. (b) ÷ (a) |
| Visual cost to users | Pixel difference % | + **SSIM** (0–1) | SSIM's definition: Wang et al. [6]. WebCloak [1] uses a different visual-similarity score (JCD), reported as average < 0.01 against 0.5261 for unrelated pages | SSIM 1.0 = identical |
| Speed cost to users | Lighthouse (median of 5) | Lighthouse performance score (0–100) and FCP, LCP, TTI, reported as **change from baseline** | WebCloak [1]: FCP, LCP, TTI and the score, as changes from the unprotected page (LCP +0.88 s, about 10%; score −0.3 to −5.5) | Google's published "good" thresholds for each Web Vital |
| Page weight (new, D71) | — | HTML size per page against baseline (bytes, %); for (c), prompt tokens per page | WebCloak [1]: HTML size (0.69 → 0.83 MB) and token count (+6.4%) | Change from baseline |
| Accessibility cost | axe-core violations; reading-order mismatch | Violations grouped by WCAG level and impact | WCAG is the accessibility standard. WebCloak [1] reports no accessibility measure (none found in the paper), so this is something our study adds | 0 new violations against baseline |

## What this means for the testbed

- **The testbed stays synthetic and local** (midterm §1: no real or third-party sites). That is its strength: we know every correct value and can change one defense at a time. Its weakness is that the studies below use real sites, so raw scores are not directly comparable.
- **So we compare effects, not raw scores.** "Shuffling cut recall from 100% to 5.7% for source-order scrapers" can sit next to "WebCloak cut recall from 88.7% to 0%" even though the sites differ.
- **We say what kind of pages and scrapers these are.** The pages are product and article pages with labelled attribute fields, like SWDE's verticals (for example, Auto: model, price, engine). The scrapers form a ladder that maps onto the classes these studies test:
  - (a) is "LLM-assisted scripting" with BeautifulSoup in [2], on a "simple HTML" site; in WebCloak's terms [1] it is closest to a script (their "LLM-to-script" class), except that a person wrote it;
  - (b) is a headless browser;
  - (c) is an LLM reading page text, closest to WebCloak's "LLM-native crawlers" such as Crawl4AI [1];
  - (d) checks visibility and CSS order on the rendered page. WebCloak found that structural defenses (full-code obfuscation, dynamic JavaScript loading, static tag renaming) are bypassed by agents that work on the final, rendered DOM [1]. That is the same capability-matching idea our hypothesis tests with (d).
- **Our honeypot is a recognised tool.** Shy Guys [4] uses a honeypot as its source of known bot traffic, "which real users have no reason to access". Our trap link follows the same reasoning.
- **Every comparison row states the differences**: the site, the number of pages, the models, the defense design.
- **No reference scraping tool** (D69): every comparison with outside work goes through layers 1–3, not by running other people's tools on our site.

## Related-work table (verified against the papers; our column is filled on Nov 25)

| Study | Setting | Scrapers or detectors | Defense | Metric | Their result | Ours, same metric | Main differences |
|---|---|---|---|---|---|---|---|
| WebCloak [1] (IEEE S&P 2026) | LLMCrawlBench: 237 real pages from 50 high-traffic sites, 5 categories; a 27-page hardest subset for comparing defenses; a small extra set with text and audio targets | 32 LLM-driven scrapers in 3 classes: LLM-to-script (e.g. Gemini-2.5-pro writing code), LLM-native crawlers (e.g. Crawl4AI), LLM web agents (e.g. Browser-Use) | Dynamic structural obfuscation + optimized semantic labyrinth; compared with full-code obfuscation, dynamic JS loading, static tag renaming and naive warning text | Scraping recall and precision; Lighthouse FCP/LCP/TTI and score; JCD visual similarity; a user study (N=35); HTML size and tokens | Recall 88.7% → 0% (hardest subset, average over agents); full benchmark 57.5%, 62.5%, 54.4% → 0.0% for the three leading agents; text targets also → 0% ("preliminary"); LCP +0.88 s; JCD < 0.01; 91% of users satisfied | Shuffling against (a)/(b): recall 100% → 5.7% (94% reduction); (c), (d) to come; Lighthouse and HTML-size changes to come | They protect mainly **images** (text only on a small extra set); real pages; frontier models (Gemini, GPT-4o, Claude, DeepSeek) vs our small local model; no accessibility measure; they ran a user study, we do not (midterm §1) |
| Beyond BeautifulSoup [2] (AAAI 2026, per the paper's copyright line) | 35 real sites in 5 tiers, from simple HTML to CAPTCHA | BeautifulSoup and Scrapy scripts written with LLM help; Claude and Simular.ai as agents | None (measures the site's own protections) | ESR (3 trials); execution time | Simple HTML: BeautifulSoup 0.93, Scrapy 0.82, Claude and Simular.ai 1.00. Scripts under 2 s; agents 10–20 s (15–20× slower) | (a) on baseline: ESR 1.00 (3/3); (b) ≈ 2× slower than (a) | Real sites; runs are whole tasks (log in, reach a page, extract), not 70 scored fields |
| FreeDOM [3] (KDD 2020) on SWDE | 8 verticals × 10 real sites; 3–5 fields per vertical | Learned extractors that must generalise to unseen sites | None | Page-level F1 per field (top-1 value) | 82.3–92.6 F1 with 1–5 seed sites (mean of 80 experiments); rendering-based baseline 84.3–88.6 | Baseline F1 for (a)–(d) | Theirs learn **unseen** sites; ours are written for our own template, so 1.0 on baseline is expected (an upper bound, not a competing score) |
| Shy Guys [4] (arXiv 2026) | 4.6 million real requests, 54,945 user agents; honeypot traffic as bot ground truth | Real bots and humans | Passive detection from user agent and favicon requests | True positive rate at a false-positive rate | 67.6% of bots caught at 3.0% FPR; existing tools about 12–18% at 0.0–0.1% | Honeypot detection rate per scraper, and FPR from the human-like visitor | Real mixed traffic vs our own scrapers; they **classify** traffic, our trap **identifies** link-following crawlers |
| FP-Inconsistent [5] (arXiv, 2025) | A honey site; 507,080 requests from 20 paid bot services | Evasive bots; DataDome and BotD as detectors | Their fingerprint-consistency checks | Detection, evasion and true-negative rates | DataDome caught 55.44%, BotD 47.07% (evasion 52.93% and 44.56%); their method cuts evasion by 44.95–48.11% at 96.84% TNR | Evasion rate of (d) against the honeypot (expected 100%) | Commercial evasive bots vs our own scrapers; fingerprinting vs a link trap |

Notes:
- [1] was read from the full paper (SP26_WebAgent.pdf) and its project page.
- [2]–[6] were read from the papers Joseph supplied. Numbers are quoted as reported.

## Analysis rules (unchanged from the midterm)

The mean and min–max over 3 runs per cell; no significance claims at n = 3; the "reduces" and "stops" (10%) rules. No single combined score: protection and user cost are plotted on two axes, one point per defense.

## References

1. X. Li, T. Qiu, Y. Jin, L. Wang, H. Guo, X. Jia, X. Wang, W. Dong. "WebCloak: Characterizing and Mitigating the Threats of LLM-Driven Web Agents as Intelligent Scrapers." IEEE S&P 2026. https://web-cloak.github.io/
2. A. Bhardwaj, N. Diwan, G. Wang. "Beyond BeautifulSoup: Benchmarking LLM-Powered Web Scraping for Everyday Users." arXiv:2601.06301, 2026.
3. B. Y. Lin, Y. Sheng, N. Vo, S. Tata. "FreeDOM: A Transferable Neural Architecture for Structured Information Extraction on Web Documents." KDD 2020. arXiv:2010.10755.
4. R. Van Boxem, T. Barbette, C. Pelsser, R. Sadre. "Shy Guys: A Light-Weight Approach to Detecting Robots on Websites." arXiv:2603.28546, 2026.
5. H. Venugopalan, S. Munir, S. Ahmed, T. Wang, S. T. King, Z. Shafiq. "FP-Inconsistent: Measurement and Analysis of Fingerprint Inconsistencies in Evasive Bot Traffic." arXiv:2406.07647, 2025.
6. Z. Wang, A. C. Bovik, H. R. Sheikh, E. P. Simoncelli. "Image Quality Assessment: From Error Visibility to Structural Similarity." IEEE Transactions on Image Processing, 13(4), 2004.
