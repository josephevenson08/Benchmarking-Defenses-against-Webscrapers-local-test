"""One graph per metric (D104), for slides and reports. Simple matplotlib, meant to be read and changed.

Graphs: recall (accuracy), precision, success rate, drop in recall, detection and evasion rate, SSIM, Lighthouse change,
HTML size change.

    python measurement/metric_graphs.py --cells results/2026-11-20-results-all/cells.csv \
                                        --cost results/2026-11-20-user-cost-full/cost.csv --out results/<date>-metric-graphs

Inputs: cells.csv from scoring/results.py (one row per scraper and site) and cost.csv from measurement/user_cost.py
(one row per site). Writes one PNG per metric. Where a published study reports the same metric, the graph draws its
number as a dashed reference line (values as quoted in docs/metrics-plan.md).

To add a graph: copy one of the calls at the bottom of main() and change the column name and labels.
"""
import argparse
import csv
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # draw to files, no window
import matplotlib.pyplot as plt

SCRAPERS = ["a", "b", "c", "d"]
NAMES = {"a": "(a) raw HTML", "b": "(b) browser", "c": "(c) LLM", "d": "(d) adaptive"}
SITES = ["baseline", "shuffled", "honeypot"]
COLORS = {"baseline": "#2a78d6", "shuffled": "#eb6834", "honeypot": "#1baf7a"}  # same colours as figures.py
GREY = "#52514e"
MEASURE_COLORS = ["#52514e", "#898781", "#c3c2b7"]  # greys for FCP, LCP, TTI, so they are not confused with sites


def read_rows(path, key):
    """A CSV file as {key value: row}, with numbers turned into floats."""
    rows = {}
    for row in csv.DictReader(open(path, encoding="utf-8")):
        for k, v in row.items():
            try:
                row[k] = float(v)
            except (TypeError, ValueError):
                pass  # text stays text; empty cells stay ""
        rows[key(row)] = row
    return rows


def label(fmt, value):
    """The value as text; a value that rounds to zero prints as 0, never -0."""
    text = fmt.format(value)
    return fmt.format(0.0) if float(re.sub(r"[^0-9.]", "", text) or 0) == 0 else text


def tidy(ax, title, ylabel):
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold")
    ax.set_ylabel(ylabel)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e1e0d9")
    ax.set_axisbelow(True)


def reference(ax, value, text):
    """A dashed line for a published number."""
    ax.axhline(value, color=GREY, linestyle="--", linewidth=1)
    ax.text(ax.get_xlim()[1], value, " " + text, va="center", ha="left", fontsize=8, color=GREY)


def scraper_graph(cells, column, sites, title, ylabel, out, scale=1.0, ymax=None, ref=None, fmt="{:.2f}"):
    """Grouped bars: one group per scraper, one bar per site."""
    fig, ax = plt.subplots(figsize=(7.5, 4))
    width = 0.8 / len(sites)
    for i, site in enumerate(sites):
        xs = [n + (i - (len(sites) - 1) / 2) * width for n in range(len(SCRAPERS))]
        values = [scale * cells[(s, site)][column] if (s, site) in cells and cells[(s, site)][column] != "" else 0
                  for s in SCRAPERS]
        ax.bar(xs, values, width * 0.9, color=COLORS[site], label=site)
        for x, v in zip(xs, values):
            ax.text(x, v, label(fmt, v), ha="center", va="bottom", fontsize=8)
    ax.set_xticks(range(len(SCRAPERS)), [NAMES[s] for s in SCRAPERS])
    if ymax:
        ax.set_ylim(0, ymax)
    tidy(ax, title, ylabel)
    if ref:
        reference(ax, *ref)
    ax.legend(frameon=False, ncols=len(sites), loc="upper left", bbox_to_anchor=(0, -0.08))
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print("wrote", out)


def detection_graph(cells, out):
    """One bar per scraper: the share of its honeypot runs that were caught (detection) and that got away (evasion)."""
    fig, ax = plt.subplots(figsize=(7.5, 4))
    caught = [100 * cells[(s, "honeypot")]["detection_rate"] for s in SCRAPERS]
    evaded = [100 - c for c in caught]
    xs = range(len(SCRAPERS))
    ax.bar(xs, caught, 0.55, color=COLORS["honeypot"], label="detection rate (caught)")
    ax.bar(xs, evaded, 0.55, bottom=caught, color="#c3c2b7", label="evasion rate (got away)")
    for x, c, e in zip(xs, caught, evaded):
        if c:
            ax.text(x, c / 2, f"caught\n{c:.0f}%", ha="center", va="center", fontsize=8, color="white")
        if e:
            ax.text(x, c + e / 2, f"evaded\n{e:.0f}%", ha="center", va="center", fontsize=8)
    ax.set_xticks(list(xs), [NAMES[s] for s in SCRAPERS])
    ax.set_ylim(0, 115)
    tidy(ax, "Honeypot: detection and evasion rate", "Share of the scraper's runs (%)")
    reference(ax, 67.6, "Shy Guys\ndetection: 67.6%")
    ax.legend(frameon=False, ncols=2, loc="upper left", bbox_to_anchor=(0, -0.08))
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print("wrote", out)


def site_graph(cost, columns, title, ylabel, out, fmt="{:.2f}", ref=None):
    """Bars per defended site (shuffled, honeypot); several columns become grouped bars."""
    sites = [s for s in ("shuffled", "honeypot") if s in cost]
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    width = 0.8 / len(columns)
    for i, (column, name) in enumerate(columns):
        xs = [n + (i - (len(columns) - 1) / 2) * width for n in range(len(sites))]
        values = [cost[s][column] if cost[s][column] != "" else 0 for s in sites]
        ax.bar(xs, values, width * 0.9, label=name if len(columns) > 1 else None,
               color=[COLORS[s] for s in sites] if len(columns) == 1 else MEASURE_COLORS[i])
        for x, v in zip(xs, values):
            ax.text(x, v, label(fmt, v), ha="center", va="bottom" if v >= 0 else "top", fontsize=8)
    ax.set_xticks(range(len(sites)), sites)
    ax.axhline(0, color=GREY, linewidth=0.8)
    tidy(ax, title, ylabel)
    if ref:
        reference(ax, *ref)
    if len(columns) > 1:
        ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print("wrote", out)


def main():
    parser = argparse.ArgumentParser(description="One graph per metric")
    parser.add_argument("--cells", required=True, help="cells.csv from scoring/results.py")
    parser.add_argument("--cost", required=True, help="cost.csv from measurement/user_cost.py")
    parser.add_argument("--out", required=True, help="folder for the PNG files")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cells = read_rows(args.cells, key=lambda r: (r["scraper"], r["condition"]))
    cost = read_rows(args.cost, key=lambda r: r["condition"])

    # Scraping metrics: one group of bars per scraper, one bar per site
    scraper_graph(cells, "recall_mean", SITES, "Recall (accuracy)", "Recall (0\u20131)", out / "1-recall.png", ymax=1.15)
    scraper_graph(cells, "precision_mean", SITES, "Precision", "Precision (0\u20131)", out / "2-precision.png", ymax=1.15)
    scraper_graph(cells, "esr", SITES, "Success rate (runs with all 70 fields right)", "Success rate (0\u20131)",
                  out / "3-success-rate.png", ymax=1.15, ref=(0.82, "Beyond BeautifulSoup:\n0.82\u20131.00"))
    scraper_graph(cells, "reduction_recall", ["shuffled", "honeypot"], "Drop in recall (accuracy) from each defense",
                  "Drop in recall (%)", out / "4-drop-in-recall.png", scale=100, ymax=115, ref=(100, "WebCloak:\n100%"), fmt="{:.1f}%")
    detection_graph(cells, out / "5-detection-evasion.png")

    # Cost to visitors: one bar (or group) per defended site
    site_graph(cost, [("ssim_mean", "SSIM")], "SSIM (1 = looks identical)", "SSIM", out / "6-ssim.png", fmt="{:.3f}")
    site_graph(cost, [("lh_fcp_ms_change_mean", "FCP"), ("lh_lcp_ms_change_mean", "LCP"), ("lh_tti_ms_change_mean", "TTI")],
               "Lighthouse change in load times", "Change (ms)", out / "7-lighthouse.png", fmt="{:+.0f}",
               ref=(880, "WebCloak LCP:\n+880 ms"))
    site_graph(cost, [("html_change_percent", "HTML size")], "HTML size change", "Change (%)",
               out / "8-html-size.png", fmt="{:+.1f}%")

if __name__ == "__main__":
    main()
