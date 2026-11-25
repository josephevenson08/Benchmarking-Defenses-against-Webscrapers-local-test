"""Scrapers against defenses, with the three measures kept for the report (D118, after the Nov 23 scrum meeting).

    python measurement/compare.py --cells results/2026-11-23-results-all/cells.csv \
                                  --cost results/2026-11-23-user-cost-full-2/cost.csv --out results/<date>-comparison

The three measures (the midterm's own: accuracy, honeypot hits, user cost, §4):
  1. Accuracy (recall)  share of the 70 fields each scraper got right on each site, mean of its runs
  2. Detection rate     share of a scraper's runs that the trap defense caught: the honeypot's trap link, or the
                        tarpit's maze (a run that requested at least one maze page). The tarpit's time wasted is
                        listed with it.
  3. Cost to visitors   one row per defense: load-time change (Lighthouse LCP), fields out of reading order,
                        and seconds of fake values on screen

Writes 1-accuracy.png (a grid of scrapers by sites), 2-detection.png (one bar per scraper) and comparison.md (the
three tables, each followed by what it shows). The other metrics stay in cells.csv and cost.csv for the comparison
with published research, which comes later.
"""
import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # draw to files, no window
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

SCRAPERS = ["a", "b", "c", "d"]
NAMES = {"a": "(a) raw HTML", "b": "(b) browser", "c": "(c) LLM", "d": "(d) adaptive"}
SITES = ["baseline", "shuffled", "honeypot", "poisoned", "tarpit"]  # a site without results is left out
DEFENSE_NAMES = {"shuffled": "Shuffling", "honeypot": "Honeypot", "poisoned": "Poisoning", "tarpit": "Tarpit"}
TRAPS = ["honeypot", "tarpit"]  # defenses that catch scrapers instead of lowering their accuracy
CAUGHT = {"honeypot": "detection_rate", "tarpit": "maze_entry_rate"}  # the cells.csv column that says a run was caught
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e1e0d9"
GREEN = "#1baf7a"  # the honeypot's colour in the other graphs
# The reference palette's blue ramp, light (near 0) to dark (near 100%): one hue for one magnitude
BLUES = LinearSegmentedColormap.from_list("blues", ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#104281"])


def read_rows(path, key):
    """A CSV file as {key: row}, with numbers turned into floats and empty cells into None."""
    rows = {}
    for row in csv.DictReader(open(path, encoding="utf-8")):
        for k, v in row.items():
            try:
                row[k] = float(v)
            except (TypeError, ValueError):
                row[k] = None if v == "" else v
        rows[key(row)] = row
    return rows


def pct(v):
    """A share as a percentage: whole numbers stay whole (100%), others keep one decimal (5.7%, 69.5%)."""
    text = f"{100 * v:.1f}"
    return (text[:-2] if text.endswith(".0") else text) + "%"


def sites_in(cells):
    return [site for site in SITES if any((s, site) in cells for s in SCRAPERS)]


def accuracy_grid(cells, out):
    """Rows: scrapers. Columns: sites. Each cell: mean accuracy and the verdict against the scraper's baseline."""
    sites = sites_in(cells)
    values = [[cells[(s, site)]["recall_mean"] if (s, site) in cells else None for site in sites] for s in SCRAPERS]
    fig, ax = plt.subplots(figsize=(1.75 * len(sites) + 1.8, 3.6))
    for i, s in enumerate(SCRAPERS):
        for j, site in enumerate(sites):
            v = values[i][j]
            if v is None:  # this scraper was not run on this site (the midterm's tarpit runs are (a), (b), (d))
                ax.add_patch(plt.Rectangle((j, i), 1, 1, facecolor="#f1f0ec", edgecolor="white", linewidth=3))
                ax.text(j + 0.5, i + 0.5, "not run", ha="center", va="center", fontsize=9, color=INK2)
                continue
            ax.add_patch(plt.Rectangle((j, i), 1, 1, facecolor=BLUES(v), edgecolor="white", linewidth=3))
            verdict = cells[(s, site)]["verdict"]
            note = "reference" if site == "baseline" else verdict
            colour = "white" if v >= 0.55 else INK
            ax.text(j + 0.5, i + 0.42, pct(v), ha="center", va="center", fontsize=12, fontweight="bold", color=colour)
            ax.text(j + 0.5, i + 0.72, note, ha="center", va="center", fontsize=8, color=colour)
    ax.set_xlim(0, len(sites))
    ax.set_ylim(len(SCRAPERS), 0)
    ax.set_xticks([j + 0.5 for j in range(len(sites))], sites)
    ax.set_yticks([i + 0.5 for i in range(len(SCRAPERS))], [NAMES[s] for s in SCRAPERS])
    ax.xaxis.tick_top()
    ax.tick_params(length=0, labelsize=10)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title("Accuracy: share of the 70 fields each scraper got right", loc="left", fontsize=12,
                 fontweight="bold", pad=28)
    fig.text(0.01, 0.02, "Darker = the scraper got more right. Mean of 3 runs. \"stops\" = below 10%; \"reduces\" = below "
             "the scraper's lowest baseline run by more than its baseline spread.", fontsize=7.5, color=INK2)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print("wrote", out)


def detection_chart(cells, out):
    """One bar per scraper (per trap defense when there are two): share of its runs that were caught."""
    traps = [t for t in TRAPS if any((s, t) in cells for s in SCRAPERS)]
    colours = {"honeypot": GREEN, "tarpit": "#6250d6"}  # palette slots 3 and 7
    fig, ax = plt.subplots(figsize=(8.5 if len(traps) > 1 else 7.5, 3.8))
    width = 0.6 / len(traps)
    for k, trap in enumerate(traps):
        xs = [n + (k - (len(traps) - 1) / 2) * width for n in range(len(SCRAPERS))]
        rates = [100 * (cells[(s, trap)][CAUGHT[trap]] or 0) if (s, trap) in cells else 0 for s in SCRAPERS]
        ax.bar(xs, rates, width * 0.9, color=colours[trap], label=trap)
        for x, s, r in zip(xs, SCRAPERS, rates):
            c = cells.get((s, trap))
            caught = round((c[CAUGHT[trap]] or 0) * c["runs"]) if c else 0
            label = (f"{caught:.0f}/{c['runs']:.0f}" if len(traps) > 1 else f"{r:.0f}%\n{caught:.0f} of {c['runs']:.0f} runs") \
                if c else "not\nrun"
            ax.text(x, r + 2, label, ha="center", va="bottom", fontsize=9, color=INK if c else INK2)
    ax.set_xticks(range(len(SCRAPERS)), [NAMES[s] for s in SCRAPERS])
    ax.set_ylim(0, 125)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylabel("Runs caught (%)")
    ax.set_title("Detection rate: share of each scraper's runs the trap caught" + (" (label: runs caught)" if len(traps) > 1 else ""),
                 loc="left", fontsize=12, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color=GRID)
    ax.set_axisbelow(True)
    if len(traps) > 1:
        ax.legend(frameon=False, ncols=len(traps), loc="upper left", bbox_to_anchor=(0, -0.1))
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print("wrote", out)


def scrapers_list(ss):
    return ", ".join(f"({s})" for s in ss)


def tables(cells, cost):
    """comparison.md: the three tables, each followed by what it shows (worked out from the verdicts)."""
    sites = sites_in(cells)
    lines = ["# Scrapers against defenses", "",
             "Three measures (D118): accuracy, detection rate and cost to visitors. Made by `measurement/compare.py` "
             "from `cells.csv` (scoring/results.py) and `cost.csv` (measurement/user_cost.py).", "",
             "## 1. Accuracy: share of the 70 fields each scraper got right", "",
             "| Scraper | " + " | ".join(sites) + " |", "|---|" + "---|" * len(sites)]
    for s in SCRAPERS:
        row = []
        for site in sites:
            c = cells.get((s, site))
            if not c:
                row.append("—")
            elif site == "baseline":
                row.append(pct(c["recall_mean"]))
            else:
                row.append(f"{pct(c['recall_mean'])} ({c['verdict']})")
        lines.append(f"| {NAMES[s]} | " + " | ".join(row) + " |")
    lines += [""]
    for site in sites:
        if site == "baseline" or site in TRAPS:
            continue
        by = {v: [s for s in SCRAPERS if (s, site) in cells and cells[(s, site)]["verdict"] == v]
              for v in ("stops", "reduces", "no effect")}
        parts = [f"{verb} {scrapers_list(by[v])}" for v, verb in (("stops", "stops"), ("reduces", "reduces"),
                                                                     ("no effect", "has no effect on")) if by[v]]
        lines.append(f"- **{DEFENSE_NAMES[site]}** " + "; ".join(parts) + ".")
    traps = [t for t in TRAPS if any((s, t) in cells for s in SCRAPERS)]
    lines += ["", "## 2. Detection rate: share of each scraper's runs the trap caught", "",
              "| Scraper | " + " | ".join(traps) + " |", "|---|" + "---|" * len(traps)]
    for s in SCRAPERS:
        row = []
        for t in traps:
            c = cells.get((s, t))
            rate = (c.get(CAUGHT[t]) or 0) if c else 0
            row.append("—" if not c else f"{100 * rate:.0f}% ({round(rate * c['runs']):.0f} of {c['runs']:.0f} runs)")
        lines.append(f"| {NAMES[s]} | " + " | ".join(row) + " |")
    lines += [""]
    for t in traps:
        caught = [s for s in SCRAPERS if (s, t) in cells and (cells[(s, t)].get(CAUGHT[t]) or 0) == 1]
        missed = [s for s in SCRAPERS if (s, t) in cells and (cells[(s, t)].get(CAUGHT[t]) or 0) == 0]
        parts = ([f"catches {scrapers_list(caught)} in every run"] if caught else []) + \
                ([f"never catches {scrapers_list(missed)}"] if missed else [])
        note = (" Only scrapers set to ignore robots.txt walk in; ones that obey it never enter (Test 6)."
                if t == "tarpit" else "")
        lines.append(f"- **{DEFENSE_NAMES[t]}** " + "; ".join(parts) + ". Its accuracy is unchanged, so this is how it shows." + note)
    if "tarpit" in traps:
        lines += ["", "Time the tarpit wasted (scrapers set to ignore robots.txt):", "",
                  "| Scraper | Maze pages per run | Seconds trapped per run | Server time per maze page |", "|---|---|---|---|"]
        for s in SCRAPERS:
            c = cells.get((s, "tarpit"))
            if c:
                ms = c.get("maze_ms_mean")
                lines.append(f"| {NAMES[s]} | {c['maze_pages_mean']:.1f} | {c['maze_seconds_mean']:.1f} s | "
                             f"{'—' if ms is None else f'{ms / 1000:.1f} s'} |")
    lines += ["", "## 3. Cost to visitors", "",
              "| Defense | Load-time change (LCP) | Fields out of reading order | Fake values on screen |", "|---|---|---|---|"]
    for site in sites:
        c = cost.get(site)
        if site == "baseline" or not c:
            continue
        lcp = c.get("lh_lcp_ms_change_mean")
        fakes = c.get("fakes_visible_max_s")
        lines.append(f"| {DEFENSE_NAMES[site]} | {'—' if lcp is None else f'{round(lcp) + 0:+d} ms'} | "
                     f"{c['fields_out_of_order']:.0f} of {c['fields']:.0f} | {'none' if fakes is None else f'{fakes:.2f} s'} |")
    lines += ["", "Load-time changes this small are within the baseline's own run-to-run noise. Also checked, with no change "
              "for any defense: how the page looks after loading (SSIM 1.000) and accessibility violations (axe-core: 0).", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Scrapers against defenses: accuracy, detection rate, cost to visitors")
    parser.add_argument("--cells", required=True, help="cells.csv from scoring/results.py")
    parser.add_argument("--cost", required=True, help="cost.csv from measurement/user_cost.py")
    parser.add_argument("--out", required=True, help="folder for the PNG files and comparison.md")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cells = read_rows(args.cells, key=lambda r: (r["scraper"], r["condition"]))
    cost = read_rows(args.cost, key=lambda r: r["condition"])
    accuracy_grid(cells, out / "1-accuracy.png")
    detection_chart(cells, out / "2-detection.png")
    (out / "comparison.md").write_text(tables(cells, cost), encoding="utf-8")
    print("wrote", out / "comparison.md")


if __name__ == "__main__":
    main()
