"""User-cost runner (midterm §4 item 4, §5 "User cost"; D70, D71; schedule Fri Nov 20 and Sat Nov 21).

    python measurement/user_cost.py [--conditions shuffled honeypot] [--out results/<date>-user-cost] [--wait 3]
                                    [--lighthouse-runs 5] [--no-axe] [--port 3200]

For the baseline and each condition, it rebuilds the site from the data list and opens every page from its files
in headless Chromium (1280x800 viewport, no server, so no request log is touched). After --wait seconds (§5: 3 s,
so poisoned pages show their real values) it takes a full-page screenshot and records where each field's label
and value sit on screen. Then, against the baseline:

  pixel difference   % of pixels that differ (pixelmatch, measurement/pixel_diff.mjs, as in Test 4)
  SSIM               structural similarity (Wang et al. 2004), same script; 1.0 = identical
  reading order      fields whose label or value is at a different position in the source than on screen,
                     divided by the fields on the page (§5: "the fraction of fields whose source position
                     differs from their top-to-bottom position on screen"). Positions count the label and value
                     elements of the fields block: source position = order in the HTML, screen position = order
                     sorted top to bottom, then left to right. Labels are paired with values as on the baseline.
  HTML size          bytes of each page file, and the change from the baseline (D71)
  axe-core           accessibility violations found by axe-core on each page after the wait (§5: counted per
                     condition), by impact and by WCAG level, and how many are new against the baseline
  Lighthouse         performance score, FCP, LCP and TTI: the median of --lighthouse-runs runs per page (§5: 5),
                     with the site served on --port, as changes from the baseline (D70; measurement/lighthouse.mjs)

axe-core and Lighthouse need `npm install` (both are pinned in package.json). --lighthouse-runs 0 skips Lighthouse.

Writes to the results folder:
  screenshots/<condition>/   one PNG per page; screenshots/diff-<condition>/ the pixel differences
  pixel-<condition>.json     the pixel-diff and SSIM report per page
  axe-<condition>.json       every axe-core violation per page
  lighthouse-<condition>.json every Lighthouse run per page, and the medians
  logs/                      the request logs of the Lighthouse servers (kept apart from scraper logs)
  pages.csv                  one row per condition and page
  cost.csv                   one row per condition (the midterm's CostMeasurement)
  report.md, manifest.json
"""

import argparse
import csv
import datetime
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DEFAULT_CONDITIONS = ["shuffled", "honeypot"]
AXE_SCRIPT = ROOT / "node_modules" / "axe-core" / "axe.min.js"
AXE_RUN = """async () => (await axe.run(document, { resultTypes: ['violations'] })).violations.map((v) => (
  { id: v.id, impact: v.impact, tags: v.tags, nodes: v.nodes.length }))"""
IMPACTS = ["critical", "serious", "moderate", "minor"]
LEVELS = ["A", "AA", "AAA", "best-practice"]
LH_MEASURES = ["score", "fcp_ms", "lcp_ms", "tti_ms"]

# Runs in the page: every label and value element of the fields block, in source order, with its screen position.
FIELD_ELEMENTS = """() => Array.from(document.querySelectorAll('main .fields .label, main .fields .value')).map((el) => {
  const r = el.getBoundingClientRect();
  return { kind: el.classList.contains('label') ? 'label' : 'value', text: el.innerText.trim(),
           top: r.top + window.scrollY, left: r.left + window.scrollX };
})"""


def screen_order(elements):
    """The elements sorted top to bottom, then left to right (positions rounded to whole pixels)."""
    return sorted(elements, key=lambda e: (round(e["top"]), round(e["left"])))


def pairs_of(sequence):
    """(label text, value text) for every label directly followed by a value: the baseline's fields."""
    return [(a["text"], b["text"]) for a, b in zip(sequence, sequence[1:]) if a["kind"] == "label" and b["kind"] == "value"]


def reading_order(source, pairs):
    """(fields, fields out of order) for one page. A field is in order when its label and its value are each at
    the same position in the source as on screen. A label or value that can't be found counts as out of order."""
    on_screen = screen_order(source)
    src = {(e["kind"], e["text"]): i for i, e in reversed(list(enumerate(source)))}
    scr = {(e["kind"], e["text"]): i for i, e in reversed(list(enumerate(on_screen)))}
    out = 0
    for label, value in pairs:
        keys = [("label", label), ("value", value)]
        if not all(k in src and src[k] == scr[k] for k in keys):
            out += 1
    return len(pairs), out


def html_sizes(condition, conditions_dir):
    """{page path: bytes of its file} for one generated condition."""
    from measurement.screenshots import load_pages
    site = Path(conditions_dir) / condition
    return {p["path"]: (site / p["file"]).stat().st_size for p in load_pages(condition, conditions_dir)}


def wcag_level(tags):
    """'A', 'AA' or 'AAA' from an axe rule's tags (wcag2a, wcag21aa, ...); 'best-practice' otherwise."""
    levels = {t.split("wcag", 1)[1].lstrip("0123456789") for t in tags if t.startswith("wcag") and t[4:5].isdigit()}
    for level in ("A", "AA", "AAA"):
        if level.lower() in levels:
            return level
    return "best-practice"


def visit_pages(condition, conditions_dir, shots_dir, wait, width=1280, height=800, run_axe=True):
    """Screenshots every page of a condition. Returns ({page path: field elements in source order},
    {page path: axe-core violations}); the second is empty when run_axe is False."""
    from playwright.sync_api import sync_playwright
    from measurement.screenshots import load_pages, png_name
    if run_axe and not AXE_SCRIPT.exists():
        raise SystemExit(f"axe-core is not installed ({AXE_SCRIPT}). Run: npm install")
    site = Path(conditions_dir) / condition
    shots_dir = Path(shots_dir)
    shots_dir.mkdir(parents=True, exist_ok=True)
    fields, axe = {}, {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        for entry in load_pages(condition, conditions_dir):
            page.goto((site / entry["file"]).resolve().as_uri(), wait_until="load")
            page.wait_for_timeout(wait * 1000)
            page.screenshot(path=str(shots_dir / png_name(entry["path"])), full_page=True)
            fields[entry["path"]] = page.evaluate(FIELD_ELEMENTS)
            if run_axe:
                page.add_script_tag(path=str(AXE_SCRIPT))
                axe[entry["path"]] = page.evaluate(AXE_RUN)
        browser.close()
    return fields, axe


def chromium_path():
    """Playwright's Chromium, which Lighthouse also uses, so no separate Chrome is needed."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        path = p.chromium.executable_path
    if not Path(path).exists():
        raise SystemExit(f"Lighthouse needs Playwright's Chromium at {path}. Run: python -m playwright install chromium")
    return path


def lighthouse_report(condition, paths, port, runs, out_dir):
    """Serves the condition on `port` and runs measurement/lighthouse.mjs on every page."""
    import os
    from measurement.test6 import start_server
    (out_dir / "logs").mkdir(exist_ok=True)
    json_file = out_dir / f"lighthouse-{condition}.json"
    server = start_server(condition, port, out_dir / "logs" / f"lighthouse-{condition}.jsonl")
    try:
        cmd = ["node", str(ROOT / "measurement" / "lighthouse.mjs"), "--base", f"http://127.0.0.1:{port}",
               "--paths", ",".join(paths), "--runs", str(runs), "--json", str(json_file)]
        run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env={**os.environ, "CHROME_PATH": chromium_path()})
    finally:
        server.terminate()
        server.wait(timeout=10)
    if not json_file.exists():
        raise SystemExit("lighthouse.mjs failed:\n" + run.stdout + run.stderr)
    return json.loads(json_file.read_text(encoding="utf-8"))


def pixel_report(baseline_dir, other_dir, diff_dir, json_file):
    cmd = ["node", str(ROOT / "measurement" / "pixel_diff.mjs"), str(baseline_dir), str(other_dir),
           "--diff-dir", str(diff_dir), "--json", str(json_file)]
    run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if not Path(json_file).exists():
        raise SystemExit("pixel_diff.mjs failed:\n" + run.stdout + run.stderr)
    return json.loads(Path(json_file).read_text(encoding="utf-8"))


def axe_counts(violations):
    """{rule id: nodes} for one page's violations."""
    return {v["id"]: v["nodes"] for v in violations}


def page_rows(condition, sizes, base_sizes, fields, base_fields, pixels, axe=None, base_axe=None, lh=None, base_lh=None):
    from measurement.screenshots import png_name
    per_png = {p["page"]: p for p in (pixels or {}).get("pages", [])}
    lh_pages = {p["path"]: p["median"] for p in (lh or {}).get("pages", [])}
    base_lh_pages = {p["path"]: p["median"] for p in (base_lh or {}).get("pages", [])}
    rows = []
    for path, size in sizes.items():
        n, out = reading_order(fields.get(path, []), pairs_of(base_fields.get(path, [])))
        px = per_png.get(png_name(path), {})
        base = base_sizes.get(path)
        row = {
            "condition": condition, "page": path, "html_bytes": size,
            "html_change_percent": None if not base else 100 * (size - base) / base,
            "pixel_diff_percent": px.get("percent"), "ssim": px.get("ssim"),
            "fields": n, "fields_out_of_order": out,
        }
        if axe is not None:
            mine, theirs = axe_counts(axe.get(path, [])), axe_counts((base_axe or {}).get(path, []))
            row["axe_violations"] = sum(mine.values())
            row["axe_new_vs_baseline"] = sum(max(0, k - theirs.get(rule, 0)) for rule, k in mine.items())
            row["axe_rules"] = " ".join(f"{rule}:{k}" for rule, k in sorted(mine.items()))
            for v in axe.get(path, []):
                key = f"axe_{v['impact'] or 'unknown'}"
                row[key] = row.get(key, 0) + v["nodes"]
                key = f"axe_level_{wcag_level(v['tags'])}"
                row[key] = row.get(key, 0) + v["nodes"]
        if lh is not None:
            m, b = lh_pages.get(path, {}), base_lh_pages.get(path, {})
            for k in LH_MEASURES:
                row[f"lh_{k}"] = m.get(k)
                row[f"lh_{k}_change"] = None if m.get(k) is None or b.get(k) is None else m[k] - b[k]
        rows.append(row)
    return rows


def condition_row(condition, rows, pixels, base_total):
    fields = sum(r["fields"] for r in rows)
    out = sum(r["fields_out_of_order"] for r in rows)
    html = sum(r["html_bytes"] for r in rows)
    changes = [r["html_change_percent"] for r in rows if r["html_change_percent"] is not None]
    return {
        "condition": condition, "pages": len(rows),
        "pixel_diff_mean_percent": pixels["mean_percent"] if pixels else None,
        "pixel_diff_max_percent": pixels["max_percent"] if pixels else None,
        "ssim_mean": pixels["mean_ssim"] if pixels else None,
        "ssim_min": pixels["min_ssim"] if pixels else None,
        "fields": fields, "fields_out_of_order": out,
        "reading_order_mismatch_rate": out / fields if fields else None,
        "html_bytes": html,
        "html_change_percent": 100 * (html - base_total) / base_total if base_total else None,
        "html_change_max_page_percent": max(changes) if changes else None,
        **axe_totals(rows), **lighthouse_means(rows),
    }


def axe_totals(rows):
    if not any("axe_violations" in r for r in rows):
        return {}
    totals = {"axe_violations": sum(r.get("axe_violations", 0) for r in rows),
              "axe_new_vs_baseline": sum(r.get("axe_new_vs_baseline", 0) for r in rows)}
    for impact in IMPACTS:
        totals[f"axe_{impact}"] = sum(r.get(f"axe_{impact}", 0) for r in rows)
    for level in LEVELS:
        totals[f"axe_level_{level}"] = sum(r.get(f"axe_level_{level}", 0) for r in rows)
    return totals


def lighthouse_means(rows):
    """Mean over the pages of each page's median, and the mean change from baseline."""
    if not any("lh_score" in r for r in rows):
        return {}
    out = {}
    for k in LH_MEASURES:
        values = [r[f"lh_{k}"] for r in rows if r.get(f"lh_{k}") is not None]
        changes = [r[f"lh_{k}_change"] for r in rows if r.get(f"lh_{k}_change") is not None]
        out[f"lh_{k}_mean"] = sum(values) / len(values) if values else None
        out[f"lh_{k}_change_mean"] = sum(changes) / len(changes) if changes else None
    return out


COST_COLUMNS = ["condition", "pages", "pixel_diff_mean_percent", "pixel_diff_max_percent", "ssim_mean", "ssim_min",
                "fields", "fields_out_of_order", "reading_order_mismatch_rate", "html_bytes", "html_change_percent",
                "html_change_max_page_percent", "axe_violations", "axe_new_vs_baseline"] + \
               [f"axe_{i}" for i in IMPACTS] + [f"axe_level_{lv}" for lv in LEVELS] + \
               [f"lh_{k}_{s}" for k in LH_MEASURES for s in ("mean", "change_mean")]
PAGE_COLUMNS = ["condition", "page", "html_bytes", "html_change_percent", "pixel_diff_percent", "ssim", "fields",
                "fields_out_of_order", "axe_violations", "axe_new_vs_baseline", "axe_rules"] + \
               [f"lh_{k}{s}" for k in LH_MEASURES for s in ("", "_change")]


def write_csv(path, columns, rows):
    def cell(v):
        if v is None:
            return ""
        return f"{v:.6g}" if isinstance(v, float) else v
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(columns)
        for r in rows:
            w.writerow([cell(r.get(c)) for c in columns])


def write_report(out_dir, manifest, cost):
    def f(v, fmt):
        return "—" if v is None else format(v, fmt)
    lines = ["# User cost", "",
             f"Run {manifest['started_at']} → {manifest['finished_at']} · commit {manifest['commit']} · "
             f"viewport {manifest['viewport']} · screenshots {manifest['wait_seconds']} s after load", "",
             "## Visual, reading order and page weight", "",
             "| Condition | Pixel diff (mean / max) | SSIM (mean / min) | Reading-order mismatch | HTML size change |",
             "|---|---|---|---|---|"]
    for c in cost:
        if c["condition"] == "baseline":
            lines.append(f"| baseline | reference | reference | {c['fields_out_of_order']}/{c['fields']} fields = "
                         f"{f(c['reading_order_mismatch_rate'], '.3f')} | {c['html_bytes']} bytes (reference) |")
            continue
        lines.append(
            f"| {c['condition']} | {f(c['pixel_diff_mean_percent'], '.3f')}% / {f(c['pixel_diff_max_percent'], '.3f')}% | "
            f"{f(c['ssim_mean'], '.4f')} / {f(c['ssim_min'], '.4f')} | "
            f"{c['fields_out_of_order']}/{c['fields']} fields = {f(c['reading_order_mismatch_rate'], '.3f')} | "
            f"{f(c['html_change_percent'], '+.1f')}% (max page {f(c['html_change_max_page_percent'], '+.1f')}%) |")
    if any("axe_violations" in c for c in cost):
        lines += ["", "## Accessibility (axe-core, all 10 pages)", "",
                  "| Condition | Violations | New vs baseline | Critical / serious / moderate / minor | WCAG A / AA / AAA / best practice |",
                  "|---|---|---|---|---|"]
        for c in cost:
            lines.append(f"| {c['condition']} | {c['axe_violations']} | {c['axe_new_vs_baseline'] if c['condition'] != 'baseline' else 'reference'} | "
                         + " / ".join(str(c[f"axe_{i}"]) for i in IMPACTS) + " | "
                         + " / ".join(str(c[f"axe_level_{lv}"]) for lv in LEVELS) + " |")
    if any("lh_score_mean" in c for c in cost):
        lh = manifest.get("lighthouse", {})
        lines += ["", f"## Speed (Lighthouse {lh.get('version')}, {lh.get('settings')}, median of {lh.get('runs_per_page')} runs per page, "
                  "mean over the 10 pages)", "",
                  "| Condition | Score | FCP | LCP | TTI |", "|---|---|---|---|---|"]
        for c in cost:
            def cell(k, unit, d):
                mean, change = c.get(f"lh_{k}_mean"), c.get(f"lh_{k}_change_mean")
                if c["condition"] == "baseline" or change is None:
                    return f"{f(mean, d)}{unit}"
                change = round(change, int(d[1:-1])) + 0.0  # so a tiny negative change prints +0, not -0
                return f"{f(mean, d)}{unit} ({f(change, '+' + d)}{unit})"
            lines.append(f"| {c['condition']} | {cell('score', '', '.1f')} | {cell('fcp_ms', ' ms', '.0f')} | "
                         f"{cell('lcp_ms', ' ms', '.0f')} | {cell('tti_ms', ' ms', '.0f')} |")
    lines += ["", "Per page: `pages.csv`. Definitions: `measurement/user_cost.py`.", ""]
    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="User-cost measures for each condition against the baseline")
    parser.add_argument("--conditions", nargs="+", default=DEFAULT_CONDITIONS, help="conditions to compare with baseline")
    parser.add_argument("--out", help="results folder (default results/<today>-user-cost)")
    parser.add_argument("--wait", type=float, default=3.0, help="seconds to wait after load (default 3)")
    parser.add_argument("--lighthouse-runs", type=int, default=5, help="Lighthouse runs per page, median kept (default 5; 0 skips)")
    parser.add_argument("--no-axe", action="store_true", help="skip axe-core")
    parser.add_argument("--port", type=int, default=3200, help="port for the Lighthouse server (default 3200)")
    args = parser.parse_args()

    from measurement.run_experiment import tool_versions
    from measurement.screenshots import load_pages
    from measurement.test4 import generate, git_commit

    out_dir = Path(args.out) if args.out else ROOT / "results" / f"{datetime.date.today().isoformat()}-user-cost"
    if out_dir.exists() and any(out_dir.iterdir()):
        raise SystemExit(f"{out_dir} already has files. Choose another --out so earlier measurements are not mixed in.")
    out_dir.mkdir(parents=True, exist_ok=True)
    conditions_dir = ROOT / "conditions"
    versions = tool_versions()
    for package in ("axe-core", "lighthouse"):
        pkg = ROOT / "node_modules" / package / "package.json"
        versions[package] = json.loads(pkg.read_text(encoding="utf-8"))["version"] if pkg.exists() else "not installed"
    manifest = {"measurement": "user cost", "started_at": datetime.datetime.now().isoformat(timespec="seconds"),
                "commit": git_commit(), "viewport": "1280x800", "wait_seconds": args.wait,
                "conditions": ["baseline"] + args.conditions, "versions": versions,
                "config": json.loads((ROOT / "config.json").read_text(encoding="utf-8"))}

    sizes, fields, axe, lighthouse = {}, {}, {}, {}
    for condition in manifest["conditions"]:
        print(f"{condition}: generating, screenshots, field positions" + ("" if args.no_axe else ", axe-core") + " ...", flush=True)
        generate(condition)
        sizes[condition] = html_sizes(condition, conditions_dir)
        fields[condition], axe[condition] = visit_pages(condition, conditions_dir, out_dir / "screenshots" / condition,
                                                        args.wait, run_axe=not args.no_axe)
        if not args.no_axe:
            (out_dir / f"axe-{condition}.json").write_text(json.dumps(axe[condition], indent=2) + "\n", encoding="utf-8")
        if args.lighthouse_runs > 0:
            paths = [p["path"] for p in load_pages(condition, conditions_dir)]
            print(f"{condition}: Lighthouse, {args.lighthouse_runs} runs on each of {len(paths)} pages ...", flush=True)
            lighthouse[condition] = lighthouse_report(condition, paths, args.port, args.lighthouse_runs, out_dir)
            manifest["lighthouse"] = {"version": lighthouse[condition]["lighthouse_version"],
                                      "settings": lighthouse[condition]["settings"], "runs_per_page": args.lighthouse_runs}

    all_pages, cost = [], []
    for condition in manifest["conditions"]:
        pixels = None
        if condition != "baseline":
            print(f"{condition}: pixel difference and SSIM against baseline ...", flush=True)
            pixels = pixel_report(out_dir / "screenshots" / "baseline", out_dir / "screenshots" / condition,
                                  out_dir / "screenshots" / f"diff-{condition}", out_dir / f"pixel-{condition}.json")
        rows = page_rows(condition, sizes[condition], sizes["baseline"], fields[condition], fields["baseline"], pixels,
                         axe=None if args.no_axe else axe[condition], base_axe=None if args.no_axe else axe["baseline"],
                         lh=lighthouse.get(condition), base_lh=lighthouse.get("baseline"))
        all_pages += rows
        cost.append(condition_row(condition, rows, pixels, sum(sizes["baseline"].values())))

    manifest["finished_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    write_csv(out_dir / "pages.csv", PAGE_COLUMNS, all_pages)
    write_csv(out_dir / "cost.csv", COST_COLUMNS, cost)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    write_report(out_dir, manifest, cost)
    print()
    print((out_dir / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
