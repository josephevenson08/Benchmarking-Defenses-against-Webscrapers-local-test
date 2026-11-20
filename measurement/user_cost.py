"""User-cost runner, part 1 (midterm §4 item 4, §5 "User cost"; D70, D71; schedule Fri Nov 20).

    python measurement/user_cost.py [--conditions shuffled honeypot] [--out results/<date>-user-cost] [--wait 3]

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

Lighthouse and axe-core are added in part 2.

Writes to the results folder:
  screenshots/<condition>/   one PNG per page; screenshots/diff-<condition>/ the pixel differences
  pixel-<condition>.json     the pixel-diff and SSIM report per page
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


def visit_pages(condition, conditions_dir, shots_dir, wait, width=1280, height=800):
    """Screenshots every page of a condition and returns {page path: field elements in source order}."""
    from playwright.sync_api import sync_playwright
    from measurement.screenshots import load_pages, png_name
    site = Path(conditions_dir) / condition
    shots_dir = Path(shots_dir)
    shots_dir.mkdir(parents=True, exist_ok=True)
    fields = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        for entry in load_pages(condition, conditions_dir):
            page.goto((site / entry["file"]).resolve().as_uri(), wait_until="load")
            page.wait_for_timeout(wait * 1000)
            page.screenshot(path=str(shots_dir / png_name(entry["path"])), full_page=True)
            fields[entry["path"]] = page.evaluate(FIELD_ELEMENTS)
        browser.close()
    return fields


def pixel_report(baseline_dir, other_dir, diff_dir, json_file):
    cmd = ["node", str(ROOT / "measurement" / "pixel_diff.mjs"), str(baseline_dir), str(other_dir),
           "--diff-dir", str(diff_dir), "--json", str(json_file)]
    run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if not Path(json_file).exists():
        raise SystemExit("pixel_diff.mjs failed:\n" + run.stdout + run.stderr)
    return json.loads(Path(json_file).read_text(encoding="utf-8"))


def page_rows(condition, sizes, base_sizes, fields, base_fields, pixels):
    from measurement.screenshots import png_name
    per_png = {p["page"]: p for p in (pixels or {}).get("pages", [])}
    rows = []
    for path, size in sizes.items():
        n, out = reading_order(fields.get(path, []), pairs_of(base_fields.get(path, [])))
        px = per_png.get(png_name(path), {})
        base = base_sizes.get(path)
        rows.append({
            "condition": condition, "page": path, "html_bytes": size,
            "html_change_percent": None if not base else 100 * (size - base) / base,
            "pixel_diff_percent": px.get("percent"), "ssim": px.get("ssim"),
            "fields": n, "fields_out_of_order": out,
        })
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
    }


COST_COLUMNS = ["condition", "pages", "pixel_diff_mean_percent", "pixel_diff_max_percent", "ssim_mean", "ssim_min",
                "fields", "fields_out_of_order", "reading_order_mismatch_rate", "html_bytes", "html_change_percent",
                "html_change_max_page_percent"]
PAGE_COLUMNS = ["condition", "page", "html_bytes", "html_change_percent", "pixel_diff_percent", "ssim", "fields",
                "fields_out_of_order"]


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
    lines = ["# User cost, part 1", "",
             f"Run {manifest['started_at']} → {manifest['finished_at']} · commit {manifest['commit']} · "
             f"viewport {manifest['viewport']} · screenshots {manifest['wait_seconds']} s after load", "",
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
    lines += ["", "Per page: `pages.csv`. Definitions: `measurement/user_cost.py`. Lighthouse and axe-core come in part 2.", ""]
    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="User-cost measures for each condition against the baseline (part 1)")
    parser.add_argument("--conditions", nargs="+", default=DEFAULT_CONDITIONS, help="conditions to compare with baseline")
    parser.add_argument("--out", help="results folder (default results/<today>-user-cost)")
    parser.add_argument("--wait", type=float, default=3.0, help="seconds to wait after load (default 3)")
    args = parser.parse_args()

    from measurement.run_experiment import tool_versions
    from measurement.test4 import generate, git_commit

    out_dir = Path(args.out) if args.out else ROOT / "results" / f"{datetime.date.today().isoformat()}-user-cost"
    if out_dir.exists() and any(out_dir.iterdir()):
        raise SystemExit(f"{out_dir} already has files. Choose another --out so earlier measurements are not mixed in.")
    out_dir.mkdir(parents=True, exist_ok=True)
    conditions_dir = ROOT / "conditions"
    manifest = {"measurement": "user cost, part 1", "started_at": datetime.datetime.now().isoformat(timespec="seconds"),
                "commit": git_commit(), "viewport": "1280x800", "wait_seconds": args.wait,
                "conditions": ["baseline"] + args.conditions, "versions": tool_versions(),
                "config": json.loads((ROOT / "config.json").read_text(encoding="utf-8"))}

    sizes, fields = {}, {}
    for condition in manifest["conditions"]:
        print(f"{condition}: generating, screenshots and field positions ...", flush=True)
        generate(condition)
        sizes[condition] = html_sizes(condition, conditions_dir)
        fields[condition] = visit_pages(condition, conditions_dir, out_dir / "screenshots" / condition, args.wait)

    all_pages, cost = [], []
    for condition in manifest["conditions"]:
        pixels = None
        if condition != "baseline":
            print(f"{condition}: pixel difference and SSIM against baseline ...", flush=True)
            pixels = pixel_report(out_dir / "screenshots" / "baseline", out_dir / "screenshots" / condition,
                                  out_dir / "screenshots" / f"diff-{condition}", out_dir / f"pixel-{condition}.json")
        rows = page_rows(condition, sizes[condition], sizes["baseline"], fields[condition], fields["baseline"], pixels)
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
