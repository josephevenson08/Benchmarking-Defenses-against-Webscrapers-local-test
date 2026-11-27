"""Test 3: the extraction rule (midterm §5, Test 3).

    python measurement/test3.py [--out results/<date>-test3] [--scrapers a b d] [--fixtures <folder>]

Each case is a folder in measurement/fixtures/test3/ with:

  page.html         a saved copy of one page, so the case never changes under the test
  expected.json     what the label-then-next-element rule should return on that page,
                    worked out by hand (Joseph):
                    {"path": "/products/p2", "records": [{"field": "name", "value": "..."}, ...]}
  expected-d.json   (optional) the same for scraper (d), when it should differ: (d) applies the rule in
                    on-screen order and reads the page after it settles, so on a shuffled or poisoned page
                    it should get the real values. Without it, (d) is held to expected.json.
  serve/            (optional) more files to serve, at their path under serve/: a poisoned page's
                    real values, serve/values/products/p1.json, are served at /values/products/p1.json

For each case the harness serves the page on its own, at its real path (plus a
robots.txt that allows everything and the files in serve/), runs each scraper on it
with --page-cap 1, and compares the records the scraper wrote for that page with its
expected file: the same fields with the same values, nothing missing and nothing extra.

Writes report.md, report.json and each scraper's output to the results folder.
Exits with 1 if a case fails or has no expected records yet.
"""

import argparse
import datetime
import http.server
import json
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "measurement" / "fixtures" / "test3"
SCRAPERS = {"a": "scrapers/a_raw_html.py", "b": "scrapers/b_browser_text.py", "d": "scrapers/d_adaptive.py"}
ROBOTS = b"User-agent: *\nDisallow:\n"


def serve_one_page(path, html, extra=None):
    """Serves html at path, an allow-all robots.txt and any extra {path: bytes} (JSON) on a free port; the rest is 404."""
    routes = {path: ("text/html; charset=utf-8", html), "/robots.txt": ("text/plain", ROBOTS)}
    routes.update({p: ("application/json", body) for p, body in (extra or {}).items()})

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            route = routes.get(self.path.split("?")[0])
            self.send_response(200 if route else 404)
            body = route[1] if route else b"Not found"
            self.send_header("Content-Type", route[0] if route else "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def compare_records(expected, actual):
    """Compares lists of {field, value}; returns missing, extra and wrong fields."""
    exp = {r["field"]: r["value"] for r in expected}
    act = {r["field"]: r["value"] for r in actual}
    return {
        "missing": sorted(f for f in exp if f not in act),
        "extra": sorted(f for f in act if f not in exp),
        "wrong": sorted(
            ({"field": f, "expected": exp[f], "got": act[f]} for f in exp if f in act and exp[f] != act[f]),
            key=lambda d: d["field"],
        ),
        "duplicates": len(actual) != len(act),
    }


def load_cases(fixtures):
    cases = []
    for folder in sorted(Path(fixtures).iterdir()):
        if not (folder / "page.html").exists() or not (folder / "expected.json").exists():
            continue
        expected = json.loads((folder / "expected.json").read_text(encoding="utf-8"))
        per_scraper = {}
        for f in folder.glob("expected-*.json"):
            per_scraper[f.stem.split("-", 1)[1]] = json.loads(f.read_text(encoding="utf-8")).get("records", [])
        serve = folder / "serve"
        extra = {"/" + f.relative_to(serve).as_posix(): f.read_bytes() for f in sorted(serve.rglob("*")) if f.is_file()} \
            if serve.exists() else {}
        cases.append({"name": folder.name, "path": expected["path"], "records": expected.get("records", []),
                      "per_scraper": per_scraper, "extra": extra, "html": (folder / "page.html").read_bytes()})
    return cases


def run_case(case, scraper, out_dir):
    server = serve_one_page(case["path"], case["html"], case.get("extra"))
    port = server.server_address[1]
    out_file = out_dir / "outputs" / f"{scraper}-{case['name']}.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        run = subprocess.run(
            [sys.executable, SCRAPERS[scraper], "--start-url", f"http://127.0.0.1:{port}{case['path']}",
             "--page-cap", "1", "--run-id", f"test3-{scraper}-{case['name']}", "--out", str(out_file)],
            cwd=ROOT, capture_output=True, text=True, timeout=120,
        )
    finally:
        server.shutdown()
        server.server_close()
    if run.returncode != 0 or not out_file.exists():
        return {"case": case["name"], "scraper": scraper, "passed": False,
                "error": (run.stdout + run.stderr).strip()[-2000:]}
    output = json.loads(out_file.read_text(encoding="utf-8"))
    records = [{"field": r["field"], "value": r["value"]} for r in output["records"] if r["page"] == case["path"]]
    expected = case.get("per_scraper", {}).get(scraper, case["records"])
    diff = compare_records(expected, records)
    pages_ok = [(p["path"], p["status"]) for p in output["pages"]] == [(case["path"], 200)]
    passed = bool(expected) and pages_ok and not (diff["missing"] or diff["extra"] or diff["wrong"] or diff["duplicates"])
    return {"case": case["name"], "scraper": scraper, "path": case["path"], "expected_records": len(expected),
            "expected_file": f"expected-{scraper}.json" if scraper in case.get("per_scraper", {}) else "expected.json",
            "records": len(records), "pages_ok": pages_ok, **diff, "passed": passed}


def write_report(out_dir, report):
    (out_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Test 3: the extraction rule",
        "",
        f"Run {report['run_at']} · commit {report['commit']}",
        "",
        "| Case | Scraper | Expected file | Expected records | Got | Missing | Extra | Wrong value | |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in report["results"]:
        if "error" in r:
            lines.append(f"| `{r['case']}` | ({r['scraper']}) | | | | | | scraper failed | FAIL |")
            continue
        wrong = ", ".join(f"{w['field']}: expected \"{w['expected']}\", got \"{w['got']}\"" for w in r["wrong"]) or "—"
        note = "" if r["expected_records"] else " (no records yet)"
        lines.append(
            f"| `{r['case']}` | ({r['scraper']}) | `{r['expected_file']}` | {r['expected_records']}{note} | {r['records']} | "
            f"{', '.join(r['missing']) or '—'} | {', '.join(r['extra']) or '—'} | {wrong} | "
            f"{'PASS' if r['passed'] else 'FAIL'} |"
        )
    lines += [
        "",
        f"**Test 3 ({', '.join(f'({s})' for s in report['scrapers'])}): {'PASS' if report['passed'] else 'FAIL'}**",
        "",
        "Each case's page is served on its own and each scraper runs with `--page-cap 1`. "
        "Scraper outputs are in `outputs/`.",
        "",
    ]
    for r in report["results"]:
        if "error" in r:
            lines += [f"Error from ({r['scraper']}) on `{r['case']}`:", "", "```", r["error"], "```", ""]
    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except OSError:
        return "unknown"


def main():
    parser = argparse.ArgumentParser(description="Test 3: the extraction rule")
    parser.add_argument("--out", help="results folder (default: results/<today>-test3)")
    parser.add_argument("--scrapers", nargs="+", default=["a", "b", "d"], choices=sorted(SCRAPERS))
    parser.add_argument("--fixtures", default=str(FIXTURES), help="folder of test cases")
    args = parser.parse_args()

    out_dir = Path(args.out) if args.out else ROOT / "results" / f"{datetime.date.today().isoformat()}-test3"
    out_dir.mkdir(parents=True, exist_ok=True)
    cases = load_cases(args.fixtures)
    if not cases:
        raise SystemExit(f"No test cases (page.html + expected.json) in {args.fixtures}")

    results = []
    for case in cases:
        for scraper in args.scrapers:
            print(f"({scraper}) on {case['name']} ...")
            results.append(run_case(case, scraper, out_dir))
    report = {
        "test": "Test 3: extraction rule",
        "run_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "commit": git_commit(),
        "scrapers": args.scrapers,
        "results": results,
        "passed": all(r["passed"] for r in results),
    }
    write_report(out_dir, report)
    print()
    print((out_dir / "report.md").read_text(encoding="utf-8"))
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
