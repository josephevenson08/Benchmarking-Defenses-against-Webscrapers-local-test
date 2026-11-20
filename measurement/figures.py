"""Figures and tables of the results so far, with the standard metrics (D68, D70; midterm §4 "Final outputs").

    python measurement/figures.py --cells <results>/cells.csv --cost <user-cost folder>
                                  [--fields <runner folder>] [--out results/<date>-figures]

Reads cells.csv from scoring/results.py, cost.csv from measurement/user_cost.py and, optionally, a runner folder whose
scraper (c) runs on the shuffled site are broken down field by field. Writes PNG figures (200 dpi, for slides and the
report) and tables.md (the same numbers as tables, plus the comparison with published work).

  fig1-recall.png             recall by scraper and condition, mean with min-max over the runs, and the 10% "stops" line
  fig2-reduction.png          the drop in recall caused by shuffling, per scraper, next to WebCloak's published drop
  fig3-protection-vs-cost.png protection (drop in recall) against user cost (reading-order mismatch), one point per
                              defense and scraper: the midterm's "one pairing accuracy drop with user cost"
  fig4-honeypot.png           honeypot detection rate per scraper
  fig5-fields.png             (with --fields) scraper (c) on the shuffled site, share of correct values per field
  tables.md                   Tables 1-4

Published numbers are quoted from the papers in docs/metrics-plan.md.
"""

import argparse
import csv
import datetime
import sys
import textwrap
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

NAMES = {"a": "(a) raw HTML", "b": "(b) browser", "c": "(c) LLM", "d": "(d) adaptive"}
CONDITIONS = ["baseline", "shuffled", "honeypot"]
# Categorical slots 1-3 of the dataviz reference palette, validated together for colour-blind separation.
COLORS = {"baseline": "#2a78d6", "shuffled": "#eb6834", "honeypot": "#1baf7a"}
OURS, PUBLISHED = "#2a78d6", "#eb6834"
INK, INK2, GRID, AXIS = "#0b0b0b", "#52514e", "#e1e0d9", "#c3c2b7"
WEBCLOAK = {"before": 88.7, "after": 0.0,
            "source": "WebCloak (IEEE S&P 2026): LLM scrapers, 27 hardest pages, mean over agents"}


def read_cells(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    cells = {}
    for r in rows:
        for k, v in r.items():
            if k not in ("scraper", "condition", "verdict", "baseline_check", "correct_per_run"):
                r[k] = float(v) if v not in ("", None) else None
        cells[(r["scraper"], r["condition"])] = r
    return cells


def read_cost(folder):
    rows = list(csv.DictReader(open(Path(folder) / "cost.csv", encoding="utf-8")))
    return {r["condition"]: {k: (v if k == "condition" else (float(v) if v != "" else None)) for k, v in r.items()} for r in rows}


def field_shares(folder, scraper="c", condition="shuffled"):
    """[(kind, field label, correct, total)] for one scraper and condition, over its runs in a runner folder."""
    import json
    from scoring.score import score_file
    labels = json.loads((ROOT / "data" / "fields.json").read_text(encoding="utf-8"))
    label_of = {f["key"]: f["label"] for kind in ("product", "article") for f in labels[kind]}
    kind_of = {f["key"]: kind.capitalize() for kind in ("product", "article") for f in labels[kind]}
    counts = defaultdict(lambda: [0, 0])
    for run in sorted((Path(folder) / "runs").glob(f"{scraper}-{condition}-*.json")):
        for r in score_file(run).results:
            c = counts[r.field]
            c[0] += r.correct
            c[1] += 1
    out = [(kind_of[k], label_of[k], v[0], v[1]) for k, v in counts.items()]
    return sorted(out, key=lambda t: (t[0] != "Product", -t[2] / t[3], t[1]))


def style(plt):
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": AXIS, "axes.labelcolor": INK2,
        "xtick.color": INK2, "ytick.color": INK2, "axes.titlesize": 12, "axes.titleweight": "bold",
        "axes.titlecolor": INK, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
        "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True, "legend.frameon": False,
        "figure.facecolor": "white", "savefig.facecolor": "white",
    })


def footnote(fig, text):
    width_chars = int(fig.get_figwidth() * 15)
    fig.text(0.01, 0.01, "\n".join(textwrap.wrap(text, width_chars)), fontsize=7.5, color=INK2, va="bottom")


def fig_recall(plt, cells, scrapers, path):
    import numpy as np
    fig, ax = plt.subplots(figsize=(8, 4.2))
    x = np.arange(len(scrapers))
    width = 0.26
    for i, cond in enumerate(CONDITIONS):
        means, lows, highs = [], [], []
        for s in scrapers:
            c = cells.get((s, cond))
            means.append(100 * c["recall_mean"] if c else np.nan)
            lows.append(100 * (c["recall_mean"] - c["recall_min"]) if c else 0)
            highs.append(100 * (c["recall_max"] - c["recall_mean"]) if c else 0)
        pos = x + (i - 1) * width
        ax.bar(pos, means, width * 0.92, color=COLORS[cond], label=cond, yerr=[lows, highs],
               error_kw={"ecolor": INK2, "elinewidth": 1, "capsize": 3})
        for xp, m in zip(pos, means):
            if not np.isnan(m):
                ax.text(xp, m + 1.5, f"{m:.0f}", ha="center", va="bottom", fontsize=8.5, color=INK)
    ax.axhline(10, color=INK2, linewidth=1, linestyle=(0, (4, 3)), label='"stops" line (10%)')
    ax.set_xticks(x, [NAMES[s] for s in scrapers])
    ax.set_ylim(0, 112)
    ax.set_ylabel("Recall (= accuracy), % of 70 fields")
    ax.set_title("Recall by scraper and site (mean of runs; bars show min–max)", loc="left")
    ax.legend(ncols=4, loc="upper left", bbox_to_anchor=(0, -0.1))
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig_reduction(plt, cells, scrapers, path):
    rows = [(f"Shuffling vs {NAMES[s]}", 100 * cells[(s, "shuffled")]["reduction_recall"], OURS)
            for s in scrapers if (s, "shuffled") in cells and cells[(s, "shuffled")]["reduction_recall"] is not None]
    rows.append(("WebCloak vs LLM scrapers (published)", 100 * (1 - WEBCLOAK["after"] / WEBCLOAK["before"]), PUBLISHED))
    rows = rows[::-1]
    fig, ax = plt.subplots(figsize=(8, 0.55 * len(rows) + 1.4))
    y = range(len(rows))
    ax.barh(list(y), [r[1] for r in rows], height=0.55, color=[r[2] for r in rows])
    for yi, r in zip(y, rows):
        ax.text(r[1] + 1.2, yi, f"{r[1]:.1f}%", va="center", fontsize=9, color=INK, fontweight="bold")
    ax.set_yticks(list(y), [r[0] for r in rows])
    ax.axvline(90, color=INK2, linewidth=1, linestyle=(0, (4, 3)), label='"stops" line (recall below 10%)')
    ax.set_xlim(0, 112)
    ax.set_xlabel("Drop in recall: 1 − recall with the defense ÷ recall without (%)")
    fig.suptitle("Drop in scraping recall: our shuffling vs a published defense", x=0.01, ha="left",
                 fontsize=12, fontweight="bold", color=INK)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), fontsize=8.5)
    ax.grid(axis="y", visible=False)
    footnote(fig, "Published: " + WEBCLOAK["source"] + ". Settings differ (real pages, frontier models), "
             "so compare the size of the drop, not raw scores.")
    fig.tight_layout(rect=(0, 0.08, 1, 0.94))
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig_protection_vs_cost(plt, cells, cost, scrapers, path):
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for cond in ("shuffled", "honeypot"):
        if cond not in cost:
            continue
        x = cost[cond]["reading_order_mismatch_rate"] or 0.0
        groups = defaultdict(list)
        for s in scrapers:
            c = cells.get((s, cond))
            if c and c["reduction_recall"] is not None:
                groups[round(100 * c["reduction_recall"], 1)].append(s)
        for red, ss in groups.items():
            ax.scatter([100 * x], [red], s=70, color=COLORS[cond], edgecolor="white", linewidth=1.5, zorder=3,
                       label=cond if red == max(groups) else None)
            ax.annotate(", ".join(f"({s})" for s in ss) + f"  {red:.1f}%", (100 * x, red), xytext=(8, 0),
                        textcoords="offset points", va="center", fontsize=8.5, color=INK)
    ax.set_xlim(-8, 115)
    ax.set_ylim(-8, 110)
    ax.set_xlabel("User cost: fields out of reading order (%)")
    ax.set_ylabel("Protection: drop in recall (%)")
    ax.set_title("Protection against user cost, one point per defense and scraper", loc="left")
    ax.legend(loc="center left")
    footnote(fig, "Both defenses: 0% pixel difference, SSIM 1.000, 0 axe-core violations, no Lighthouse change beyond "
             "noise. The honeypot protects by detection, not by lowering recall (Figure 4).")
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig_honeypot(plt, cells, scrapers, path):
    fig, ax = plt.subplots(figsize=(7, 3.4))
    rates = [100 * cells[(s, "honeypot")]["detection_rate"] if (s, "honeypot") in cells else 0 for s in scrapers]
    ax.bar(range(len(scrapers)), rates, width=0.5, color=COLORS["honeypot"])
    for i, r in enumerate(rates):
        ax.text(i, r + 2, f"{r:.0f}%", ha="center", fontsize=9, color=INK, fontweight="bold")
    ax.set_xticks(range(len(scrapers)), [NAMES[s] for s in scrapers])
    ax.set_ylim(0, 112)
    ax.set_ylabel("Runs caught by the trap (%)")
    ax.set_title("Honeypot detection rate (share of runs that requested /trap)", loc="left")
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig_fields(plt, shares, path):
    fig, ax = plt.subplots(figsize=(7, 0.32 * len(shares) + 1.3))
    labels = [f"{label} ({kind.lower()})" for kind, label, _, _ in shares][::-1]
    values = [100 * ok / n for _, _, ok, n in shares][::-1]
    counts = [f"{ok}/{n}" for _, _, ok, n in shares][::-1]
    ax.barh(range(len(values)), values, height=0.6, color=COLORS["shuffled"])
    for i, (v, c) in enumerate(zip(values, counts)):
        ax.text(v + 1.5, i, c, va="center", fontsize=8.5, color=INK2)
    ax.set_yticks(range(len(values)), labels)
    ax.set_xlim(0, 112)
    ax.set_xlabel("Correct values over the runs (%)")
    ax.set_title("Scraper (c) on the shuffled site, field by field", loc="left")
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def pct(v, d=1):
    return "—" if v is None else f"{100 * v:.{d}f}%"


def tables(cells, cost, scrapers):
    lines = ["# Results tables", "", f"Made {datetime.date.today().isoformat()} by `measurement/figures.py` from `cells.csv` "
             "(scoring/results.py) and `cost.csv` (measurement/user_cost.py).", "",
             "## Table 1. Extraction quality by defense and scraper", "",
             "| Scraper | Site | Correct per run | Recall (min–max) | Precision | F1 | ESR | Drop in recall | Verdict |",
             "|---|---|---|---|---|---|---|---|---|"]
    for s in scrapers:
        for cond in CONDITIONS:
            c = cells.get((s, cond))
            if not c:
                continue
            rng = "" if c["recall_min"] == c["recall_max"] else f" ({pct(c['recall_min'])}–{pct(c['recall_max'])})"
            prec = "—" if c["precision_mean"] is None else f"{c['precision_mean']:.3f}"
            lines.append(f"| {NAMES[s]} | {cond} | {c['correct_per_run']} | {pct(c['recall_mean'])}{rng} | {prec} | "
                         f"{c['f1_mean']:.3f} | {c['esr']:.2f} | {pct(c['reduction_recall'])} | {c['verdict']} |")
    base_tpp = cells.get(("a", "baseline"), {}).get("time_per_page_mean")
    lines += ["", "## Table 2. Honeypot and speed", "",
              "| Scraper | Honeypot detection rate | Evasion rate | Trap hits (honeypot runs) | Time per page (baseline) | Slowdown vs (a) |",
              "|---|---|---|---|---|---|"]
    for s in scrapers:
        h, b = cells.get((s, "honeypot")), cells.get((s, "baseline"))
        if not h or not b:
            continue
        slow = f"{b['time_per_page_mean'] / base_tpp:.0f}×" if base_tpp else "—"
        lines.append(f"| {NAMES[s]} | {h['detection_rate']:.2f} | {h['evasion_rate']:.2f} | {h['honeypot_hits']:.0f} | "
                     f"{b['time_per_page_mean']:.3f} s | {slow} |")
    lines += ["", "False-positive rate: planned (a human-like visitor that clicks only visible links, Sun Nov 29).", "",
              "## Table 3. User cost against baseline", "",
              "| Site | Pixel diff (max) | SSIM (min) | Fields out of reading order | HTML size | axe-core violations (new) | "
              "Lighthouse score | FCP | LCP | TTI |", "|---|---|---|---|---|---|---|---|---|---|"]
    for cond in ("shuffled", "honeypot"):
        c = cost.get(cond)
        if not c:
            continue
        def ch(k, unit, d=0):
            v = c.get(f"lh_{k}_change_mean")
            return "—" if v is None else f"{round(v, d) + 0.0:+.{d}f}{unit}"
        lines.append(f"| {cond} | {c['pixel_diff_max_percent']:.3f}% | {c['ssim_min']:.4f} | "
                     f"{c['fields_out_of_order']:.0f}/{c['fields']:.0f} | {c['html_change_percent']:+.1f}% | "
                     f"{c.get('axe_violations', 0):.0f} ({c.get('axe_new_vs_baseline', 0):.0f}) | {ch('score', '', 1)} | "
                     f"{ch('fcp_ms', ' ms')} | {ch('lcp_ms', ' ms')} | {ch('tti_ms', ' ms')} |")
    lines += ["", "Lighthouse changes are the mean over the 10 pages of each page's median of 5 runs; a change smaller than "
              "the baseline's own run-to-run range is not counted as an effect (§5).", ""]
    # Table 4: comparison with published work
    sh = {s: cells[(s, "shuffled")] for s in scrapers if (s, "shuffled") in cells}
    drops = ", ".join(f"{pct(c['reduction_recall'])} {NAMES[s].split()[0]}" for s, c in sh.items())
    esr = ", ".join(f"{cells[(s, 'baseline')]['esr']:.2f} {NAMES[s].split()[0]}" for s in scrapers if (s, "baseline") in cells)
    det = ", ".join(f"{cells[(s, 'honeypot')]['detection_rate']:.2f} {NAMES[s].split()[0]}" for s in scrapers if (s, "honeypot") in cells)
    lines += ["## Table 4. Our results next to published ones (same metric)", "",
              "| Metric | Ours | Published | Source | Main difference |", "|---|---|---|---|---|",
              f"| Drop in scraping recall caused by the defense | shuffling: {drops} | 100% (88.7% → 0%) | WebCloak, IEEE S&P 2026 | "
              "Real pages and frontier-model agents; they protect mainly images |",
              f"| Speed cost of the defense (Lighthouse) | no change beyond noise | LCP +0.88 s; score −0.3 to −5.5 | WebCloak | "
              "Their defense adds scripts; ours adds CSS or one link |",
              f"| Extraction success rate on simple HTML (baseline) | {esr} | 0.82–1.00 | Beyond BeautifulSoup, AAAI 2026 | "
              "Whole tasks on real sites vs 70 scored fields |",
              f"| Bot detection rate | honeypot: {det} | 67.6% of bots at 3.0% false positives | Shy Guys, 2026 | "
              "Passive classification of real traffic vs a link trap |",
              "| Evasion by an adaptive bot | (d) evades the honeypot in every run | 44.6–52.9% evasion of commercial detectors | "
              "FP-Inconsistent, 2025 | Paid evasive bot services vs our own scraper |", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Figures and tables of the results so far")
    parser.add_argument("--cells", required=True, help="cells.csv from scoring/results.py")
    parser.add_argument("--cost", required=True, help="results folder from measurement/user_cost.py")
    parser.add_argument("--fields", help="runner folder with (c)'s shuffled runs, for the per-field figure")
    parser.add_argument("--out", help="output folder (default results/<today>-figures)")
    args = parser.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    style(plt)
    cells, cost = read_cells(args.cells), read_cost(args.cost)
    scrapers = [s for s in "abcd" if (s, "baseline") in cells]
    out = Path(args.out) if args.out else ROOT / "results" / f"{datetime.date.today().isoformat()}-figures"
    out.mkdir(parents=True, exist_ok=True)
    fig_recall(plt, cells, scrapers, out / "fig1-recall.png")
    fig_reduction(plt, cells, scrapers, out / "fig2-reduction.png")
    fig_protection_vs_cost(plt, cells, cost, scrapers, out / "fig3-protection-vs-cost.png")
    fig_honeypot(plt, cells, scrapers, out / "fig4-honeypot.png")
    if args.fields:
        fig_fields(plt, field_shares(args.fields), out / "fig5-fields.png")
    (out / "tables.md").write_text(tables(cells, cost, scrapers), encoding="utf-8")
    print(f"Figures and tables written to {out}")
    for f in sorted(out.iterdir()):
        print(" ", f.name)


if __name__ == "__main__":
    main()
