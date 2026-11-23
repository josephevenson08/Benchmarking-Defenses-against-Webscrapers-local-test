"""Test 5: poisoning hides real values (midterm §5, Test 5).

    python measurement/test5.py [--condition poisoned] [--out results/<date>-test5] [--port 3100] [--late 3]

Rebuilds the poisoned condition from site/defenses/poisoned.js, serves it with site/server.js on its own port and
a fresh request log, and checks, in the midterm's words, that "no real value should appear in the HTML, every
field should equal its fake at 0 s, and every field should equal its real value at 3 s":

  1. Fakes file: conditions/poisoned.fakes.json has one fake for each of the 70 scored fields, and each fake is a
     valid value for its field that differs from the real one under the matching rules (scoring/score.py's
     load_fakes, the same check the scoring uses).
  2. HTML: every page's HTML, as served (view source), is searched for each of the 70 real values. A match must
     stand alone: "4.5" inside "$64.50" or "Lark" inside "Larkfield" is not a match.
  3. At 0 s: each item page is opened in Chromium (Playwright) and read right after the load event. Every field
     should show its fake.
  4. At 3 s (--late): the same page, read again 3 s after the load event. Every field should show its real value.

Fields are read as the label and value of each `.field` row, as the baseline page has them, and compared as text
(spaces trimmed). The test also records when each page's values last changed, which is how long the fakes stay
on screen (the user cost "seconds fake values stay visible", §4 item 4), and whether each page fetched its
real-values JSON (from the request log).

The answer key (data/items.json) is read here: this is a test, not a scraper.

Writes report.md, report.json and requests.jsonl to the results folder. Exits with 1 if a check fails.
"""

import argparse
import datetime
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scoring.score import DataList, load_fakes  # noqa: E402

RUN_ID = "test5"

# Each time the text inside a .value element changes, note the time (ms since the page started loading).
RECORD_CHANGES = """
(() => {
  window.__valueChanges = [];
  new MutationObserver((records) => {
    for (const r of records) {
      const el = r.target.nodeType === 1 ? r.target : r.target.parentElement;
      if (el && el.closest && el.closest(".value")) { window.__valueChanges.push(performance.now()); return; }
    }
  }).observe(document, { subtree: true, childList: true, characterData: true });
})();
"""

READ_FIELDS = """() => [...document.querySelectorAll(".field")].map((row) => ({
  label: (row.querySelector(".label") || {}).textContent || null,
  value: (row.querySelector(".value") || {}).textContent || null,
}))"""

TIMES = """() => {
  const nav = performance.getEntriesByType("navigation")[0];
  return { now: performance.now(), load: nav ? nav.loadEventEnd : null, changes: window.__valueChanges || [] };
}"""


def text(value):
    return re.sub(r"\s+", " ", str(value if value is not None else "")).strip()


def escape_html(value):
    return (str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&#39;"))


def standalone(value, html):
    """Places where value (or its HTML-escaped form) stands alone in html: not inside a longer word or number."""
    hits = []
    for form in {value, escape_html(value)}:
        pattern = r"(?<![A-Za-z0-9])" + re.escape(form) + r"(?![A-Za-z0-9])"
        hits += [m.start() for m in re.finditer(pattern, html)]
    return sorted(set(hits))


def leaks(pages_html, truth):
    """[{page, item_id, field, value, context}] for every real value found standing alone in any page's HTML."""
    found = []
    for path, html in pages_html.items():
        for (item, field), value in truth.items():
            for at in standalone(value, html):
                found.append({"page": path, "item_id": item, "field": field, "value": value,
                              "context": html[max(0, at - 40): at + len(value) + 40].replace("\n", " ")})
    return found


def compare(shown, expected):
    """Fields of one page that do not show the expected text: [{field, label, expected, shown}]."""
    by_label = {text(r["label"]): text(r["value"]) for r in shown}
    return [{"field": key, "label": label, "expected": want, "shown": by_label.get(label)}
            for key, label, want in expected if by_label.get(label) != text(want)]


def check_fakes_file(fakes_file, data):
    """Check 1. Returns (fakes {(item, field): fake}, problems [text]). Each fake is checked on its own, so one bad
    fake is listed without hiding the others, and the fakes are still returned for checks 3 and 4."""
    if not fakes_file.exists():
        return {}, [f"{fakes_file.name} was not written: does the defense file export fakeValue?"]
    entries = json.loads(fakes_file.read_text(encoding="utf-8"))
    fakes, problems = {}, []
    for entry in entries:
        try:
            load_fakes([entry], data)
        except ValueError as err:
            problems.append(str(err))
        key = (entry.get("item_id"), entry.get("field"))
        if key in fakes:
            problems.append(f"more than one fake for {key}")
        fakes[key] = entry.get("fake_value")
    problems += [f"no fake for {item} {field}" for item, field in sorted(set(data.truth) - set(fakes))]
    return fakes, problems


def read_log(log_file):
    if not log_file.exists():
        return []
    return [json.loads(line) for line in log_file.read_text(encoding="utf-8").splitlines() if line.strip()]


def run_browser(port, item_pages, late, executable_path=None):
    """Checks 3 and 4: each item page read right after load and `late` seconds after load."""
    from playwright.sync_api import sync_playwright
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(**({"executable_path": executable_path} if executable_path else {}))
        context = browser.new_context(user_agent=f"bench-test (run={RUN_ID})")
        context.add_init_script(script=RECORD_CHANGES)
        page = context.new_page()
        for entry in item_pages:
            page.goto(f"http://127.0.0.1:{port}{entry['path']}", wait_until="load")
            early = page.evaluate(READ_FIELDS)
            early_at = page.evaluate(TIMES)
            page.wait_for_timeout(max(0.0, late * 1000 - (page.evaluate(TIMES)["now"] - (early_at["load"] or 0))))
            later = page.evaluate(READ_FIELDS)
            later_at = page.evaluate(TIMES)
            results.append({"page": entry["path"], "early": early, "late": later, "read_early_ms": early_at["now"],
                            "read_late_ms": later_at["now"], "load_ms": early_at["load"],
                            "last_change_ms": max(later_at["changes"]) if later_at["changes"] else None})
        browser.close()
    return results


def start_server(condition, port, log_file):
    from measurement.test6 import start_server as start
    return start(condition, port, log_file)


def fetch(port, path):
    import http.client
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("GET", path, headers={"User-Agent": f"bench-test (run={RUN_ID}-source)"})
    body = conn.getresponse().read().decode("utf-8", errors="replace")
    conn.close()
    return body


def write_report(out_dir, report):
    (out_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    def mark(ok):
        return "PASS" if ok else "FAIL"

    c = report["checks"]
    lines = ["# Test 5: poisoning hides real values", "",
             f"Run {report['run_at']} · commit {report['commit']} · condition `{report['condition']}` · "
             f"read at 0 s (right after load) and {report['late_seconds']:g} s after load", "",
             f"**{'PASS' if report['passed'] else 'FAIL'}**", "",
             "| Check | Result | |", "|---|---|---|",
             f"| 1. Fakes file: one valid fake per field, each different from the real value | "
             f"{c['fakes_file']['fakes']} of 70 fakes" + (f"; {len(c['fakes_file']['problems'])} problems" if c['fakes_file']['problems'] else "")
             + f" | {mark(c['fakes_file']['passed'])} |",
             f"| 2. No real value in any page's HTML | {len(c['html']['leaks'])} real values found "
             f"(searched {c['html']['pages']} pages for 70 values) | {mark(c['html']['passed'])} |",
             f"| 3. Every field shows its fake at 0 s | {c['early']['matching']} of {c['early']['fields']} | {mark(c['early']['passed'])} |",
             f"| 4. Every field shows its real value at {report['late_seconds']:g} s | {c['late']['matching']} of {c['late']['fields']} | "
             f"{mark(c['late']['passed'])} |", ""]
    for problem in c["fakes_file"]["problems"][:20]:
        lines.append(f"- Fakes file: {problem}")
    if c["html"]["leaks"]:
        lines += ["", "Real values found in the HTML (the first 20):", "", "| Page | Real value of | Value | Around it |", "|---|---|---|---|"]
        for leak in c["html"]["leaks"][:20]:
            lines.append(f"| {leak['page']} | {leak['item_id']} {leak['field']} | `{leak['value']}` | `{leak['context']}` |")
    lines += ["", "## Each item page", "",
              "| Page | Fakes at 0 s | Real at 3 s | Values last changed | Fetched its real values | Fields not as expected |",
              "|---|---|---|---|---|---|"]
    for p in report["pages"]:
        wrong = [f"{w['field']} at 0 s shows `{w['shown']}`" for w in p["early_wrong"]][:2] + \
                [f"{w['field']} at 3 s shows `{w['shown']}`" for w in p["late_wrong"]][:2]
        changed = "—" if p["last_change_ms"] is None else f"{p['last_change_ms'] / 1000:.2f} s after start ({p['swap_after_load_s']:.2f} s after load)"
        lines.append(f"| {p['page']} | {p['fields'] - len(p['early_wrong'])}/{p['fields']} | {p['fields'] - len(p['late_wrong'])}/{p['fields']} | "
                     f"{changed} | {p['fetched_values']} | {'; '.join(wrong) or '—'} |")
    v = report["fakes_visible"]
    if v["max_s"] is not None:
        lines += ["", f"Fakes stay on screen until {v['max_s']:.2f} s after the page starts loading (mean {v['mean_s']:.2f} s; "
                      f"config `poison_swap_delay_seconds` = {report['config_swap_delay']})."]
    else:
        lines += ["", "On at least one page the values never changed after the page loaded, so no swap was seen there."]
    (out_dir / "report.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main():
    from measurement.test4 import git_commit
    parser = argparse.ArgumentParser(description="Test 5: poisoning hides real values")
    parser.add_argument("--condition", default="poisoned", help="the poisoned condition (default poisoned)")
    parser.add_argument("--out", help="results folder (default: results/<today>-test5)")
    parser.add_argument("--port", type=int, default=3100, help="port for the test server (default 3100)")
    parser.add_argument("--late", type=float, default=3.0, help="seconds after load for the second read (default 3)")
    parser.add_argument("--executable-path", help="a Chromium binary to use instead of Playwright's own")
    args = parser.parse_args()
    out_dir = Path(args.out) if args.out else ROOT / "results" / f"{datetime.date.today().isoformat()}-test5"
    out_dir.mkdir(parents=True, exist_ok=True)
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    data = DataList.load()

    print(f"Generating {args.condition} ...")
    built = subprocess.run(["node", str(ROOT / "site" / "generate.js"), args.condition], cwd=ROOT, capture_output=True, text=True)
    if built.returncode != 0:
        raise SystemExit("The generator stopped:\n" + built.stdout + built.stderr)
    print(built.stdout.strip())
    manifest = json.loads((ROOT / "conditions" / f"{args.condition}.manifest.json").read_text(encoding="utf-8"))
    fakes, problems = check_fakes_file(ROOT / "conditions" / f"{args.condition}.fakes.json", data)
    item_pages = [p for p in manifest["pages"] if p.get("item_id")]
    expected = {p["path"]: [(f["key"], f["label"]) for f in data_fields(p)] for p in item_pages}

    log_file = out_dir / "requests.jsonl"
    log_file.unlink(missing_ok=True)
    print(f"Serving {args.condition} on port {args.port}; reading the HTML and each item page at 0 s and {args.late:g} s ...")
    server = start_server(args.condition, args.port, log_file)
    try:
        html = {p["path"]: fetch(args.port, p["path"]) for p in manifest["pages"]}
        browser = run_browser(args.port, item_pages, args.late, args.executable_path)
        time.sleep(0.3)  # the server writes each log line when its response finishes
    finally:
        server.terminate()
        server.wait(timeout=10)
    log = read_log(log_file)

    found = leaks(html, data.truth)
    pages, early_ok, late_ok, fields = [], 0, 0, 0
    for b in browser:
        item = next(p for p in item_pages if p["path"] == b["page"])
        rows = expected[b["page"]]
        early_wrong = compare(b["early"], [(k, label, fakes.get((item["item_id"], k), "(no fake)")) for k, label in rows])
        late_wrong = compare(b["late"], [(k, label, data.truth[(item["item_id"], k)]) for k, label in rows])
        fetched = [e for e in log if e.get("run_id") == RUN_ID and e.get("path") == item.get("values")]
        fields += len(rows)
        early_ok += len(rows) - len(early_wrong)
        late_ok += len(rows) - len(late_wrong)
        swap_ms = b["last_change_ms"] if b["last_change_ms"] is not None and b["last_change_ms"] > (b["load_ms"] or 0) else None
        pages.append({"page": b["page"], "fields": len(rows), "early_wrong": early_wrong, "late_wrong": late_wrong,
                      "last_change_ms": swap_ms, "load_ms": b["load_ms"],
                      "swap_after_load_s": None if swap_ms is None else (swap_ms - (b["load_ms"] or 0)) / 1000,
                      "read_early_ms": b["read_early_ms"], "read_late_ms": b["read_late_ms"],
                      "fetched_values": f"yes ({fetched[0]['status']})" if fetched else "no"})
    swaps = [p["last_change_ms"] / 1000 for p in pages if p["last_change_ms"] is not None]
    checks = {
        "fakes_file": {"fakes": len(fakes), "problems": problems, "passed": not problems and set(fakes) == set(data.truth)},
        "html": {"pages": len(html), "leaks": found, "passed": not found},
        "early": {"fields": fields, "matching": early_ok, "passed": fields == len(data.truth) and early_ok == fields},
        "late": {"fields": fields, "matching": late_ok, "passed": fields == len(data.truth) and late_ok == fields},
    }
    report = {"test": "Test 5: poisoning hides real values", "run_at": datetime.datetime.now().isoformat(timespec="seconds"),
              "commit": git_commit(), "condition": args.condition, "late_seconds": args.late,
              "config_swap_delay": config.get("poison_swap_delay_seconds"), "checks": checks, "pages": pages,
              "fakes_visible": {"max_s": max(swaps) if len(swaps) == len(pages) and swaps else None,
                                "mean_s": sum(swaps) / len(swaps) if len(swaps) == len(pages) and swaps else None},
              "passed": all(c["passed"] for c in checks.values())}
    write_report(out_dir, report)
    print()
    print((out_dir / "report.md").read_text(encoding="utf-8"))
    sys.exit(0 if report["passed"] else 1)


def data_fields(page):
    """The fields of an item page, in order: [{key, label}] from data/fields.json."""
    fields = json.loads((ROOT / "data" / "fields.json").read_text(encoding="utf-8"))
    return fields["product" if page["type"] == "product" else "article"]


if __name__ == "__main__":
    main()
