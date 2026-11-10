"""Test 6: honeypot and logging (midterm §5, Test 6), plus checks on the honeypot pages.

    python measurement/test6.py [--out results/<date>-test6] [--port 3100] [--wait 3]

Part A, Test 6 itself. Serves the honeypot condition on its own port with a fresh
log file, then sends:
  1. one request to the trap path with run ID R,
  2. one request to a normal page with run ID R,
  3. one request with no User-Agent at all,
and one more request afterwards to show the server is still up. Expected: the trap
request logs as a hit for R, the normal page does not, and the request without a
User-Agent logs as "unknown" without crashing the server. (The tarpit part of Test 6
applies only if the tarpit is built.)

Part B, the honeypot pages (Wed Nov 11, "finish the honeypot condition"): every
page has exactly one link to the trap path, a browser does not show it, and the
pages differ from the baseline by at most --limit percent of pixels.

Writes report.md, report.json and the request log (requests.jsonl) to the results
folder. Exits with 1 if a check fails.
"""

import argparse
import datetime
import http.client
import json
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright  # noqa: E402

from measurement.test4 import check_pixels, generate, git_commit  # noqa: E402

RUN_ID = "test6"


def start_server(condition, port, log_file):
    """Starts site/server.js and waits for its 'Listening on' line (no request needed)."""
    proc = subprocess.Popen(
        ["node", str(ROOT / "site" / "server.js"), condition, "--port", str(port), "--log", str(log_file)],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    lines = queue.Queue()
    threading.Thread(target=lambda: [lines.put(line) for line in proc.stdout], daemon=True).start()
    deadline = time.time() + 15
    output = []
    while time.time() < deadline:
        try:
            line = lines.get(timeout=0.2)
        except queue.Empty:
            if proc.poll() is not None:
                break
            continue
        output.append(line)
        if line.startswith("Listening on"):
            return proc
    proc.kill()
    raise SystemExit("The server did not start:\n" + "".join(output))


def get(port, path, user_agent=None):
    """One GET request; with user_agent=None no User-Agent header is sent at all."""
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    headers = {"User-Agent": user_agent} if user_agent is not None else {}
    conn.request("GET", path, headers=headers)
    response = conn.getresponse()
    response.read()
    conn.close()
    return response.status


def read_log(log_file):
    if not Path(log_file).exists():
        return []
    return [json.loads(line) for line in Path(log_file).read_text(encoding="utf-8").splitlines() if line.strip()]


def analyse_log(entries, run_id, trap_path, normal_path):
    """Counts the log lines Test 6 cares about."""
    mine = [e for e in entries if e.get("run_id") == run_id]
    trap = [e for e in mine if e.get("path") == trap_path]
    normal = [e for e in mine if e.get("path") == normal_path]
    unknown = [e for e in entries if e.get("run_id") == "unknown"]
    return {
        "trap_lines_for_run": len(trap),
        "trap_hits_for_run": sum(1 for e in trap if e.get("honeypot_hit") is True),
        "normal_lines_for_run": len(normal),
        "normal_hits_for_run": sum(1 for e in normal if e.get("honeypot_hit") is True),
        "unknown_lines": len(unknown),
        "unknown_without_user_agent": sum(1 for e in unknown if e.get("user_agent") is None),
        "hits_for_other_runs": sum(1 for e in entries if e.get("honeypot_hit") and e.get("run_id") != run_id),
    }


def test6_passed(counts, statuses, alive):
    return (
        counts["trap_lines_for_run"] == 1 and counts["trap_hits_for_run"] == 1
        and counts["normal_lines_for_run"] == 1 and counts["normal_hits_for_run"] == 0
        and counts["unknown_lines"] == 1 and counts["unknown_without_user_agent"] == 1
        and counts["hits_for_other_runs"] == 0
        and all(status == 200 for status in statuses.values()) and alive
    )


def run_test6(port, log_file, trap_path, normal_path):
    log_file.unlink(missing_ok=True)
    proc = start_server("honeypot", port, log_file)
    try:
        statuses = {
            "trap, run R": get(port, trap_path, f"bench-test (run={RUN_ID})"),
            "normal page, run R": get(port, normal_path, f"bench-test (run={RUN_ID})"),
            "no User-Agent": get(port, "/"),
        }
        alive = proc.poll() is None
        statuses["afterwards (server still up)"] = get(port, "/products/", f"bench-test (run={RUN_ID}-alive)")
        alive = alive and proc.poll() is None
        time.sleep(0.3)  # the server writes each log line when its response finishes
    finally:
        proc.terminate()
        proc.wait(timeout=10)
    counts = analyse_log(read_log(log_file), RUN_ID, trap_path, normal_path)
    return {"run_id": RUN_ID, "trap_path": trap_path, "normal_path": normal_path, "statuses": statuses,
            "server_stayed_up": alive, "counts": counts, "passed": test6_passed(counts, statuses, alive)}


def check_trap_links(trap_path, executable_path=None):
    """Every honeypot page: exactly one link to the trap path, and the browser does not show it."""
    conditions_dir = ROOT / "conditions"
    manifest = json.loads((conditions_dir / "honeypot.manifest.json").read_text(encoding="utf-8"))
    pages = []
    with sync_playwright() as p:
        browser = p.chromium.launch(**({"executable_path": executable_path} if executable_path else {}))
        page = browser.new_page()
        for entry in manifest["pages"]:
            page.goto((conditions_dir / "honeypot" / entry["file"]).resolve().as_uri(), wait_until="load")
            links = page.locator(f'a[href="{trap_path}"]')
            count = links.count()
            hidden = count > 0 and all(not links.nth(i).is_visible() for i in range(count))
            pages.append({"page": entry["path"], "trap_links": count, "hidden": hidden})
        browser.close()
    return {"pages": pages, "passed": all(p["trap_links"] == 1 and p["hidden"] for p in pages)}


def write_report(out_dir, report):
    (out_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    t6, links, pixels = report["test6"], report["trap_links"], report["pixels"]
    c = t6["counts"]

    def mark(ok):
        return "PASS" if ok else "FAIL"

    lines = [
        "# Test 6: honeypot and logging",
        "",
        f"Run {report['run_at']} · commit {report['commit']} · trap path `{t6['trap_path']}` · run ID R = `{t6['run_id']}`",
        "",
        "## Part A: Test 6 (requests and log)",
        "",
        "| Check | Result | |",
        "|---|---|---|",
        f"| Trap request with run R logs as a hit for R | {c['trap_lines_for_run']} line, {c['trap_hits_for_run']} hit "
        f"| {mark(c['trap_lines_for_run'] == 1 and c['trap_hits_for_run'] == 1)} |",
        f"| Normal page with run R is not a hit | {c['normal_lines_for_run']} line, {c['normal_hits_for_run']} hits "
        f"| {mark(c['normal_lines_for_run'] == 1 and c['normal_hits_for_run'] == 0)} |",
        f"| Request with no User-Agent logs as `unknown` | {c['unknown_lines']} line, user_agent empty in "
        f"{c['unknown_without_user_agent']} | {mark(c['unknown_lines'] == 1 and c['unknown_without_user_agent'] == 1)} |",
        f"| Server stays up (a request afterwards gets 200) | {'yes' if t6['server_stayed_up'] else 'NO'} "
        f"| {mark(t6['server_stayed_up'] and all(s == 200 for s in t6['statuses'].values()))} |",
        f"| No other run is logged as a hit | {c['hits_for_other_runs']} | {mark(c['hits_for_other_runs'] == 0)} |",
        "| Tarpit part (robots.txt and `/maze/`) | tarpit not built | n/a |",
        "",
        f"**Test 6: {mark(t6['passed'])}**  (full request log: `requests.jsonl`)",
        "",
        "## Part B: honeypot pages",
        "",
        "| Check | Result | |",
        "|---|---|---|",
        f"| Exactly one trap link on every page | "
        f"{sum(p['trap_links'] == 1 for p in links['pages'])} of {len(links['pages'])} pages | "
        f"{mark(all(p['trap_links'] == 1 for p in links['pages']))} |",
        f"| The browser does not show it | {sum(p['hidden'] for p in links['pages'])} of {len(links['pages'])} hidden | "
        f"{mark(all(p['hidden'] for p in links['pages']))} |",
        f"| Pixel difference from baseline at most {pixels['limit_percent']}% | max {pixels['max_percent']:.3f}%, "
        f"mean {pixels['mean_percent']:.3f}% | {mark(pixels['passed'])} |",
        "",
        f"**Honeypot pages: {mark(links['passed'] and pixels['passed'])}**",
        "",
    ]
    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Test 6: honeypot and logging")
    parser.add_argument("--out", help="results folder (default: results/<today>-test6)")
    parser.add_argument("--port", type=int, default=3100, help="port for the test server (default 3100)")
    parser.add_argument("--limit", type=float, default=1.0, help="pixel difference limit in percent (default 1)")
    parser.add_argument("--wait", type=float, default=3.0, help="seconds to wait before each screenshot (default 3)")
    parser.add_argument("--executable-path", help="a Chromium binary to use instead of Playwright's own")
    args = parser.parse_args()

    out_dir = Path(args.out) if args.out else ROOT / "results" / f"{datetime.date.today().isoformat()}-test6"
    out_dir.mkdir(parents=True, exist_ok=True)
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    trap_path = config["trap_path"]

    print("Generating baseline and honeypot ...")
    generate("baseline")
    generate("honeypot")
    print(f"A. Test 6: serving honeypot on port {args.port} and sending the test requests ...")
    t6 = run_test6(args.port, out_dir / "requests.jsonl", trap_path, "/products/p1")
    print("B. Checking the trap link on every page ...")
    links = check_trap_links(trap_path, args.executable_path)
    print("   Taking screenshots and comparing pixels with the baseline (about a minute) ...")
    pixels = check_pixels("honeypot", out_dir, args.limit, args.wait, args.executable_path)

    report = {
        "test": "Test 6: honeypot and logging",
        "run_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "commit": git_commit(),
        "test6": t6,
        "trap_links": links,
        "pixels": pixels,
        "passed": t6["passed"] and links["passed"] and pixels["passed"],
    }
    write_report(out_dir, report)
    print()
    print((out_dir / "report.md").read_text(encoding="utf-8"))
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
