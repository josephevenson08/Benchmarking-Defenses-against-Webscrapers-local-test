"""Test 4: shuffling keeps the layout (midterm §5, Test 4).

    python measurement/test4.py [--condition shuffled] [--out results/<date>-test4] [--limit 1] [--wait 3]

Runs the automated part of Test 4 and saves everything in one results folder:

1. Byte-identical regeneration: the condition is generated twice with the same
   seed (into temporary folders) and every file is compared by SHA-256.
2. Source order: on every item page (6 products, 2 articles), the order of the
   label and value elements in the HTML must differ from the baseline's.
3. Pixel difference: full-page screenshots of all 10 pages of both conditions
   (measurement/screenshots.py), compared with measurement/pixel_diff.mjs; every
   page must be at most --limit percent (default 1).

The manual part is Joseph's: open pairs.html in the results folder, look at the
10 screenshot pairs, and fill in by-eye.md.

Writes report.json and report.md. Exits with 1 if any automated check fails.
"""

import argparse
import datetime
import hashlib
import json
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from measurement.screenshots import png_name, take_screenshots  # noqa: E402


class _FieldsParser(HTMLParser):
    """Collects (kind, text) for every label and value element inside div.fields."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0          # nesting depth inside div.fields (0 = outside)
        self.current = None     # "label" or "value" while inside such a span
        self.text = []
        self.sequence = []

    def handle_starttag(self, tag, attrs):
        classes = (dict(attrs).get("class") or "").split()
        if self.depth == 0:
            if tag == "div" and "fields" in classes:
                self.depth = 1
            return
        self.depth += 1
        if tag == "span" and ("label" in classes or "value" in classes):
            self.current = "label" if "label" in classes else "value"
            self.text = []

    def handle_endtag(self, tag):
        if self.depth == 0:
            return
        if tag == "span" and self.current:
            self.sequence.append((self.current, "".join(self.text).strip()))
            self.current = None
        self.depth -= 1

    def handle_data(self, data):
        if self.current:
            self.text.append(data)


def field_sequence(html):
    """The label and value elements of a page's fields block, in source order."""
    parser = _FieldsParser()
    parser.feed(html)
    return parser.sequence


def pairs_kept(baseline_seq, other_seq):
    """How many labels are still directly followed by their own value in other_seq."""
    value_of = {}
    for (kind, text), nxt in zip(baseline_seq, baseline_seq[1:]):
        if kind == "label" and nxt[0] == "value":
            value_of[text] = nxt[1]
    return sum(
        1
        for (kind, text), nxt in zip(other_seq, other_seq[1:])
        if kind == "label" and nxt == ("value", value_of.get(text))
    )


def file_hashes(folder):
    folder = Path(folder)
    return {
        str(p.relative_to(folder)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(folder.rglob("*"))
        if p.is_file()
    }


def compare_folders(a, b):
    ha, hb = file_hashes(a), file_hashes(b)
    return {
        "files": len(ha),
        "differing": sorted(f for f in ha.keys() & hb.keys() if ha[f] != hb[f]),
        "only_in_first": sorted(ha.keys() - hb.keys()),
        "only_in_second": sorted(hb.keys() - ha.keys()),
    }


def generate(condition, out_dir=None):
    cmd = ["node", str(ROOT / "site" / "generate.js"), condition]
    if out_dir:
        cmd += ["--out", str(out_dir)]
    subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True, text=True)


def git_commit():
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "site", "data", "config.json"], cwd=ROOT,
                               capture_output=True, text=True).stdout.strip()
        return commit + (" (with uncommitted changes in site/, data/ or config.json)" if dirty else "")
    except OSError:
        return "unknown"


def check_regeneration(condition):
    with tempfile.TemporaryDirectory() as tmp:
        first, second = Path(tmp, "first"), Path(tmp, "second")
        generate(condition, first)
        generate(condition, second)
        result = compare_folders(first, second)
    result["passed"] = not (result["differing"] or result["only_in_first"] or result["only_in_second"])
    return result


def check_source_order(condition, conditions_dir):
    manifest = json.loads((conditions_dir / f"{condition}.manifest.json").read_text(encoding="utf-8"))
    pages = []
    for page in manifest["pages"]:
        if page["type"] not in ("product", "article"):
            continue
        base = field_sequence((conditions_dir / "baseline" / page["file"]).read_text(encoding="utf-8"))
        other = field_sequence((conditions_dir / condition / page["file"]).read_text(encoding="utf-8"))
        pages.append({
            "page": page["path"],
            "elements": len(other),
            "same_elements": sorted(base) == sorted(other),
            "order_differs": base != other,
            "label_value_pairs_in_baseline": len(base) // 2,
            "pairs_still_adjacent": pairs_kept(base, other),
        })
    passed = bool(pages) and all(p["order_differs"] and p["same_elements"] for p in pages)
    return {"pages": pages, "passed": passed}


def check_pixels(condition, out_dir, limit, wait, executable_path):
    shots = out_dir / "screenshots"
    for cond in ("baseline", condition):
        take_screenshots(cond, shots / cond, wait=wait, executable_path=executable_path)
    report_file = out_dir / "pixel-diff.json"
    cmd = ["node", str(ROOT / "measurement" / "pixel_diff.mjs"), str(shots / "baseline"), str(shots / condition),
           "--diff-dir", str(shots / "diff"), "--json", str(report_file), "--limit", str(limit)]
    run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if not report_file.exists():
        raise SystemExit("pixel_diff.mjs failed:\n" + run.stdout + run.stderr)
    report = json.loads(report_file.read_text(encoding="utf-8"))
    pages = [{"page": p["page"], "percent": None if p.get("missing") else round(p["percent"], 4)} for p in report["pages"]]
    passed = not report["missing"] and all(p["percent"] <= limit for p in pages)
    return {"limit_percent": limit, "max_percent": report["max_percent"], "mean_percent": report["mean_percent"],
            "pages": pages, "passed": passed}


def write_pairs_page(out_dir, condition, pages):
    rows = []
    for page in pages:
        name = png_name(page)
        rows.append(
            f'<h2>{page}</h2>\n<div class="row">'
            f'<figure><img src="screenshots/baseline/{name}"><figcaption>baseline</figcaption></figure>'
            f'<figure><img src="screenshots/{condition}/{name}"><figcaption>{condition}</figcaption></figure>'
            f'<figure><img src="screenshots/diff/{name}"><figcaption>difference (red = different pixels)</figcaption></figure>'
            "</div>"
        )
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Test 4 screenshot pairs</title>
<style>body {{ font-family: system-ui, sans-serif; margin: 1rem; }} .row {{ display: flex; gap: 1rem; align-items: flex-start; }}
figure {{ margin: 0; flex: 1; }} img {{ width: 100%; border: 1px solid #ccc; }} figcaption {{ text-align: center; color: #555; }}</style>
</head><body><h1>Test 4: baseline vs {condition}, all 10 pages</h1>
{chr(10).join(rows)}
</body></html>
"""
    (out_dir / "pairs.html").write_text(html, encoding="utf-8")


def write_by_eye_template(out_dir, condition, pages):
    target = out_dir / "by-eye.md"
    if target.exists():
        return
    lines = [
        f"# Test 4: by-eye check of the 10 screenshot pairs ({condition} vs baseline)",
        "",
        "Open `pairs.html` in a browser. For each page, do the baseline and the "
        f"{condition} screenshots look the same?",
        "",
        "| Page | Look the same? (yes/no) | Notes |",
        "|---|---|---|",
    ]
    lines += [f"| `{page}` |  |  |" for page in pages]
    lines += ["", "Checked by: ", "Date: ", ""]
    target.write_text("\n".join(lines), encoding="utf-8")


def write_report(out_dir, report):
    (out_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    regen, order, pixels = report["regeneration"], report["source_order"], report["pixels"]
    def mark(ok):
        return "PASS" if ok else "FAIL"

    lines = [
        f"# Test 4: {report['condition']} keeps the layout",
        "",
        f"Run {report['run_at']} · commit {report['commit']} · config seed {report['seed']}",
        "",
        "| Check | Result | |",
        "|---|---|---|",
        f"| 1. Same seed gives byte-identical files | {regen['files']} files compared, "
        f"{len(regen['differing'])} differ | {mark(regen['passed'])} |",
        f"| 2. Source order differs from baseline on every item page | "
        f"{sum(p['order_differs'] for p in order['pages'])} of {len(order['pages'])} item pages differ | "
        f"{mark(order['passed'])} |",
        f"| 3. Pixel difference at most {pixels['limit_percent']}% | max {pixels['max_percent']:.3f}%, "
        f"mean {pixels['mean_percent']:.3f}% over {len(pixels['pages'])} pages | {mark(pixels['passed'])} |",
        "| 4. 10 screenshot pairs checked by eye | see `by-eye.md` (Joseph) | — |",
        "",
        f"**Automated part: {mark(report['passed'])}**",
        "",
        "## Source order per item page",
        "",
        "| Page | Elements | Order differs | Label still directly followed by its value |",
        "|---|---|---|---|",
    ]
    lines += [
        f"| `{p['page']}` | {p['elements']} | {'yes' if p['order_differs'] else 'NO'} | "
        f"{p['pairs_still_adjacent']} of {p['label_value_pairs_in_baseline']} |"
        for p in order["pages"]
    ]
    lines += ["", "## Pixel difference per page", "", "| Page | Different pixels |", "|---|---|"]
    for p in pixels["pages"]:
        value = "missing" if p["percent"] is None else f"{p['percent']:.3f}%"
        lines.append(f"| `{p['page']}` | {value} |")
    lines += ["", "Screenshots: `screenshots/` (1280×800 viewport, full page, "
              f"{report['wait_seconds']} s wait). Difference images: `screenshots/diff/`.", ""]
    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Test 4: shuffling keeps the layout")
    parser.add_argument("--condition", default="shuffled")
    parser.add_argument("--out", help="results folder (default: results/<today>-test4)")
    parser.add_argument("--limit", type=float, default=1.0, help="pixel difference limit in percent (default 1)")
    parser.add_argument("--wait", type=float, default=3.0, help="seconds to wait before each screenshot (default 3)")
    parser.add_argument("--executable-path", help="a Chromium binary to use instead of Playwright's own")
    args = parser.parse_args()

    out_dir = Path(args.out) if args.out else ROOT / "results" / f"{datetime.date.today().isoformat()}-test4"
    out_dir.mkdir(parents=True, exist_ok=True)
    conditions_dir = ROOT / "conditions"
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

    print("Generating baseline and", args.condition, "...")
    generate("baseline")
    generate(args.condition)
    print("1. Regenerating", args.condition, "twice with the same seed ...")
    regen = check_regeneration(args.condition)
    print("2. Comparing source order with the baseline ...")
    order = check_source_order(args.condition, conditions_dir)
    print("3. Taking screenshots and comparing pixels (about a minute) ...")
    pixels = check_pixels(args.condition, out_dir, args.limit, args.wait, args.executable_path)

    pages = [p["path"] for p in json.loads((conditions_dir / "baseline.manifest.json").read_text(encoding="utf-8"))["pages"]]
    write_pairs_page(out_dir, args.condition, pages)
    write_by_eye_template(out_dir, args.condition, pages)
    report = {
        "test": "Test 4: shuffle keeps layout",
        "condition": args.condition,
        "run_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "commit": git_commit(),
        "seed": config["seed"],
        "wait_seconds": args.wait,
        "regeneration": regen,
        "source_order": order,
        "pixels": pixels,
        "passed": regen["passed"] and order["passed"] and pixels["passed"],
    }
    write_report(out_dir, report)

    print()
    print((out_dir / "report.md").read_text(encoding="utf-8").split("## Source order")[0].strip())
    print()
    print("Next (by eye): open", out_dir / "pairs.html", "and fill in", out_dir / "by-eye.md")
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
