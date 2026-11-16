# Metrics plan: making the results comparable with other work

Decisions D68 (chat-keeper, Turn 240) and D69 (Turn 246), after the Nov 16 scrum meeting. The instructor's point: a result such as "4/70" says little on its own. A reader can't tell whether it is good or bad, typical or unusual, until it is compared with something. This plan says what each number is compared with.

Status: planned, not built yet. The scoring changes are scheduled for Fri Nov 20, the related-work table for Wed Nov 25 and the honeypot false-positive check for Sun Nov 29 (`SCHEDULE.md`). The scraper output format and the matching rules (`docs/scraper-output.md`, D31–D35) do not change.

## Three layers of comparison

1. **Against our own baseline.** Every defended result is reported next to the same scraper on the undefended site, as a **relative reduction**. This is the most portable number: it cancels out how easy or hard our site is, so it can sit next to "before → after" results from other studies.
2. **Against standard definitions and yardsticks.** Every measure is also reported in the form other work uses (precision, recall, F1, detection and false-positive rates, SSIM, Lighthouse, WCAG/axe-core). Some of these come with published thresholds that give meaning without needing another paper.
3. **Against published results.** A related-work table puts our numbers next to published ones in the same units, and says how each study's setting differs from ours.

## The measures

| What we measure | Kept from the midterm (§4) | Standard form we add | Where others use it | Outside yardstick |
|---|---|---|---|---|
| Extraction quality | Accuracy = correct ÷ 70 | Field-level **recall** (the same number as accuracy), **precision** = correct ÷ fields returned, **F1** | Web data extraction (the SWDE benchmark line reports page-level F1 per attribute); WebCloak reports recall and precision for LLM scrapers | 1.0 = everything right; compare with each study's undefended scores |
| Defense effect | "Reduces" and "stops" rules (§4) | **Relative reduction** = 1 − F1 with the defense ÷ F1 without (0 = no effect, 1 = fully stopped) | WebCloak's headline is in these terms (recall 88.7% → 0%) | The size of the drop, not the absolute score |
| Fake values (poisoning, if built) | Fake-value rate = fakes ÷ 70 | Same | — | 0 = no fakes taken |
| Honeypot | Hits per run (request log) | **Detection rate** (true positive rate) = scraper runs caught ÷ scraper runs; **false-positive rate** from a human-like visitor that clicks only visible links | Bot-detection studies report detection at a given false-positive rate (for example 67.7% at 3%) | A useful detector catches most bots at a low false-positive rate |
| Speed for the scraper | Time per page | Same, plus slowdown vs baseline | — | Ratio to the same scraper's baseline |
| Visual cost to users | Pixel difference % | + **SSIM** (0–1 structural similarity) | Image comparison and visual-regression testing | 1.0 = identical; above about 0.99 is usually invisible (rule of thumb from tools, not a standard) |
| Speed cost to users | Lighthouse (median of 5) | Lighthouse performance score (0–100) and its Core Web Vitals | Industry standard for page performance | Google's published "good" thresholds for each Web Vital |
| Accessibility cost | axe-core violations; reading-order mismatch | Violations grouped by WCAG level and impact | WCAG is the accessibility standard | 0 new violations against baseline |

## What this means for the testbed

- **The testbed stays synthetic and local** (midterm §1: no real or third-party sites). That is its strength: we know every correct value and can change one defense at a time. Its weakness is that other studies use real sites, so raw scores are not directly comparable.
- **So we compare effects, not raw scores.** "Shuffling cut F1 by 94% for source-order scrapers" can be compared with "obfuscation cut recall from 88.7% to 0%" even though the sites differ.
- **We say what kind of pages and scrapers these are.** The pages are product and article pages with labelled attribute fields, the same kind of page web-extraction benchmarks use. The scrapers form a ladder that maps onto the classes other studies test: (a) raw HTTP + parser, (b) headless browser, (c) LLM reading page text, (d) a browser that checks visibility and CSS order.
- **Every comparison row states the differences**: the site, the number of pages, the models and the defense design.
- **No reference scraping tool** (D69): every comparison with outside work goes through layers 1–3, not by running other people's tools on our site.

## Related-work table (to fill on Nov 25)

| Study | Setting | Scrapers | Defense | Metric | Their result | Our comparable result | Differences |
|---|---|---|---|---|---|---|---|
| WebCloak (IEEE S&P 2026, per search results; benchmark LLMCrawlBench) | Real high-traffic pages | 32 LLM-driven scraper variants | Structural obfuscation + "semantic labyrinth" | Scraping recall (and precision) | 88.7% → 0% | Shuffling vs (a)/(b): recall 100% → 5.7% | To verify from the paper |
| SWDE-based extraction work | Real sites, 8 verticals | Learned extractors | None | Page-level F1 | Varies by paper | Baseline F1 for (a)–(d) | To verify |
| Bot detection (e.g. "Shy Guys") | Real server logs | Real bots | User-agent and favicon heuristics | Detection rate at a false-positive rate | 67.7% at 3% | Honeypot detection and false-positive rates | To verify |

Every published number above comes from search summaries. Each one must be checked against the paper itself before it goes into the report.

## Analysis rules (unchanged from the midterm)

The mean and min–max over 3 runs per cell; no significance claims at n = 3; the "reduces" and "stops" (10%) rules. No single combined score: protection and user cost are plotted on two axes, one point per defense.
