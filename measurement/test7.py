"""Test 7: failure handling, the crawl part (midterm §5, Test 7; schedule Tue Nov 24).

    python measurement/test7.py [--scrapers a b] [--out results/<date>-test7] [--slow-seconds 12]

Serves a small test site on a free port (no defenses, no data list):

    /             links to /t7/a, /t7/missing and /t7/slow
    /t7/a         links to /t7/b
    /t7/b         links back to /t7/a and / (a link cycle)
    /t7/missing   404
    /t7/slow      answers only after --slow-seconds (12 s: longer than the scrapers' 5 s timeout and the 10 s in
                  config.json), then links to /t7/a
    /robots.txt   allows everything

Each scraper crawls it twice from /:
  1. page cap 15: it should record the 404 (status 404) and the timeout (error "timeout") and keep going, visit
     every page exactly once (no loops), and finish;
  2. page cap 3: it should stop after 3 pages.

The midterm's other part of Test 7, a stub in place of Ollama for (c) and (e), is planned for Sun Nov 29.

Writes report.md, report.json and each scraper's output and printed log to the results folder.
Exits with 1 if any check fails.
"""

import argparse
import datetime
import http.server
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SCRAPERS = {"a": "scrapers/a_raw_html.py", "b": "scrapers/b_browser_text.py", "c": "scrapers/c_llm_text.py",
            "d": "scrapers/d_adaptive.py"}
ROBOTS = b"User-agent: *\nDisallow:\n"
LINKS = {
    "/": ["/t7/a", "/t7/missing", "/t7/slow"],
    "/t7/a": ["/t7/b"],
    "/t7/b": ["/t7/a", "/"],
    "/t7/slow": ["/t7/a"],
}
ALL_PAGES = ["/", "/t7/a", "/t7/missing", "/t7/slow", "/t7/b"]


def page_html(path):
    links = "".join(f'<li><a href="{href}">{href}</a></li>' for href in LINKS[path])
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Test 7 {path}</title></head>'
            f"<body><main><h1>Test 7 page {path}</h1><ul>{links}</ul></main></body></html>").encode()


def serve_site(slow_seconds):
    """The Test 7 site on a free port; returns the server."""
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split("?")[0]
            if path == "/t7/slow":
                time.sleep(slow_seconds)
            if path == "/robots.txt":
                status, ctype, body = 200, "text/plain", ROBOTS
            elif path in LINKS:
                status, ctype, body = 200, "text/html; charset=utf-8", page_html(path)
            else:
                status, ctype, body = 404, "text/plain", b"Not found"
            try:
                self.send_response(status)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except ConnectionError:
                pass  # the scraper gave up on the slow page, which is the point (Windows reports it as ConnectionAbortedError)

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def check_full_crawl(pages):
    """Checks for the page-cap-15 crawl. Returns {check name: passed}."""
    paths = [p.get("path") for p in pages]
    by_path = {p.get("path"): p for p in pages}
    missing = by_path.get("/t7/missing", {})
    slow = by_path.get("/t7/slow", {})
    return {
        "every page visited": sorted(set(paths)) == sorted(ALL_PAGES),
        "no page visited twice (no loop)": len(paths) == len(set(paths)),
        "404 recorded": missing.get("status") == 404,
        "timeout recorded": slow.get("status") is None and slow.get("error") == "timeout",
        "kept going after the timeout": "/t7/b" in by_path,
        "other pages loaded": all(by_path.get(p, {}).get("status") == 200 and by_path[p].get("error") is None
                                  for p in ("/", "/t7/a", "/t7/b")),
    }


def check_capped_crawl(pages, cap):
    paths = [p.get("path") for p in pages]
    return {
        f"stopped at the page cap ({cap})": len(paths) == cap,
        "started at /": bool(paths) and paths[0] == "/",
        "no page visited twice": len(paths) == len(set(paths)),
    }


def run_scraper(scraper, port, cap, run_id, out_dir, timeout):
    out_file = out_dir / "outputs" / f"{run_id}.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, SCRAPERS[scraper], "--start-url", f"http://127.0.0.1:{port}/", "--page-cap", str(cap),
           "--run-id", run_id, "--out", str(out_file)]
    start = time.perf_counter()
    try:
        done = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        code, printed = done.returncode, done.stdout + done.stderr
    except subprocess.TimeoutExpired:
        code, printed = None, f"[test7] stopped after {timeout} s"
    wall = round(time.perf_counter() - start, 2)
    (out_dir / "outputs" / f"{run_id}.log").write_text(printed, encoding="utf-8")
    output = json.loads(out_file.read_text(encoding="utf-8")) if out_file.exists() else None
    return code, wall, output


def test_scraper(scraper, out_dir, slow_seconds):
    server = serve_site(slow_seconds)
    port = server.server_address[1]
    results = []
    try:
        for cap, kind in ((15, "full"), (3, "capped")):
            run_id = f"test7-{scraper}-cap{cap}"
            code, wall, output = run_scraper(scraper, port, cap, run_id, out_dir, timeout=slow_seconds * 3 + 120)
            pages = (output or {}).get("pages", [])
            checks = {"finished without crashing": code == 0 and output is not None}
            checks.update(check_full_crawl(pages) if kind == "full" else check_capped_crawl(pages, cap))
            results.append({"scraper": scraper, "run_id": run_id, "page_cap": cap, "exit_code": code, "wall_s": wall,
                            "pages": [[p.get("path"), p.get("status"), p.get("error")] for p in pages],
                            "checks": checks, "passed": all(checks.values())})
    finally:
        server.shutdown()
        server.server_close()
    return results


def write_report(out_dir, report):
    (out_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = ["# Test 7: failure handling (crawl part)", "",
             f"Run {report['run_at']} · commit {report['commit']} · slow page answers after {report['slow_seconds']} s", "",
             "| Scraper | Page cap | Pages visited (path status error) | Checks | |", "|---|---|---|---|---|"]
    for r in report["results"]:
        visited = "<br>".join(f"`{p} {s} {e or ''}`".replace(" `", "`") for p, s, e in r["pages"]) or "—"
        checks = "<br>".join(("✅ " if ok else "❌ ") + name for name, ok in r["checks"].items())
        lines.append(f"| ({r['scraper']}) | {r['page_cap']} | {visited} | {checks} | {'PASS' if r['passed'] else 'FAIL'} |")
    lines += ["", f"**Test 7, crawl part ({', '.join('(' + s + ')' for s in report['scrapers'])}): "
              f"{'PASS' if report['passed'] else 'FAIL'}**", "",
              "The test site: `/` links to `/t7/a`, `/t7/missing` (404) and `/t7/slow` (answers after the timeout); "
              "`/t7/a` → `/t7/b` → back to `/t7/a` and `/` (a cycle). Outputs and what each scraper printed are in `outputs/`. "
              "The stub-model part for (c) is separate (Sun Nov 29).", ""]
    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Test 7, crawl part: a 404, a link cycle, a slow page and a page cap")
    parser.add_argument("--scrapers", nargs="+", default=["a", "b"], choices=sorted(SCRAPERS))
    parser.add_argument("--out", help="results folder (default results/<today>-test7)")
    parser.add_argument("--slow-seconds", type=float, default=12, help="how long /t7/slow takes to answer (default 12)")
    args = parser.parse_args()
    from measurement.test4 import git_commit

    out_dir = Path(args.out) if args.out else ROOT / "results" / f"{datetime.date.today().isoformat()}-test7"
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {"test": "Test 7, crawl part", "run_at": datetime.datetime.now().isoformat(timespec="seconds"),
              "commit": git_commit(), "slow_seconds": args.slow_seconds, "scrapers": args.scrapers, "results": []}
    for scraper in args.scrapers:
        if not (ROOT / SCRAPERS[scraper]).exists():
            raise SystemExit(f"No file {SCRAPERS[scraper]} yet.")
        print(f"({scraper}) ...", flush=True)
        report["results"] += test_scraper(scraper, out_dir, args.slow_seconds)
    report["passed"] = all(r["passed"] for r in report["results"])
    write_report(out_dir, report)
    print((out_dir / "report.md").read_text(encoding="utf-8"))
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
