"""Test 7, the fake-model part for scraper (c) (midterm §5, Test 7; schedule Sun Nov 29).

    python measurement/test7_model.py [--out results/<date>-test7-model] [--port 3100] [--slow-seconds 125]

Checks (c)'s failure rules with a fake Ollama in place of the real one: each bad answer must be recorded in its own
category, and the run must keep going. The fake listens where (c) sends its requests, 127.0.0.1:11434, so the real
Ollama must not be running (quit it from its tray icon first; start it again afterwards).

The test site is the baseline condition, served with site/server.js on --port. The fake recognizes each item page
from its text (the item's name or title, from the data list) and answers:

    a2   text that isn't JSON                      -> (c) should record "invalid_json"
    p1   a JSON list instead of an object          -> "invalid_json"
    p2   an object without one of the fields       -> "missing_key"
    p3   nothing for --slow-seconds (longer than (c)'s 120 s timeout) -> "model_timeout"
    the other item pages: a correct-looking object ("stub" for every field) -> no error, values saved

Run 1 crawls the whole site with the fake. Run 2 crawls the first pages with nothing listening on 11434 (the model is
not running) and should record "model_error" on each item page. Both runs must finish (exit 0) and visit every page.

The answer key (data/items.json) is read here only to recognize pages: this is a test, not a scraper.
Writes report.md, report.json, the fake's request log and each run's output to the results folder. Exits 1 on a failure.
"""
import argparse
import datetime
import http.server
import json
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

MODEL_PORT = 11434
SCRAPER = ROOT / "scrapers" / "c_llm_text.py"
PLAN = {"a2": "not_json", "p1": "list", "p2": "missing_key", "p3": "slow"}
EXPECTED_ERROR = {"not_json": "invalid_json", "list": "invalid_json", "missing_key": "missing_key", "slow": "model_timeout"}


def port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def load_pages():
    """{item_id: (page path, the text that identifies it, its field labels)} from the data list."""
    items = json.loads((ROOT / "data" / "items.json").read_text(encoding="utf-8"))
    fields = json.loads((ROOT / "data" / "fields.json").read_text(encoding="utf-8"))
    pages = {p["product_id"]: (f"/products/{p['product_id']}", p["name"], [f["label"] for f in fields["product"]])
             for p in items["products"]}
    pages.update({a["article_id"]: (f"/articles/{a['article_id']}", a["title"], [f["label"] for f in fields["article"]])
                  for a in items["articles"]})
    return pages


def start_fake_model(pages, slow_seconds, calls):
    """A stand-in for Ollama's /api/generate that answers each item page as PLAN says."""
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            prompt = body.get("prompt", "")
            item = next((i for i, (_, text, _) in pages.items() if text in prompt), None)
            behaviour = PLAN.get(item, "good")
            calls.append({"item": item, "behaviour": behaviour, "at": time.time()})
            labels = pages[item][2] if item else []
            if behaviour == "slow":
                time.sleep(slow_seconds)
            answer = {"not_json": "this is not JSON", "list": "[1, 2, 3]",
                      "missing_key": json.dumps({label: "stub" for label in labels[1:]})}.get(
                behaviour, json.dumps({label: "stub" for label in labels}))
            reply = json.dumps({"model": body.get("model"), "response": answer, "done": True}).encode()
            try:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(reply)))
                self.end_headers()
                self.wfile.write(reply)
            except (BrokenPipeError, ConnectionError):
                pass  # the scraper gave up waiting (the timeout case)

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", MODEL_PORT), Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def run_c(port, run_id, out_dir, page_cap):
    out_file, log_file = out_dir / f"{run_id}.json", out_dir / f"{run_id}.log"
    start = time.perf_counter()
    done = subprocess.run([sys.executable, str(SCRAPER), "--start-url", f"http://127.0.0.1:{port}/", "--run-id", run_id,
                           "--out", str(out_file), "--page-cap", str(page_cap)],
                          cwd=ROOT, capture_output=True, text=True, timeout=1200)
    log_file.write_text(done.stdout + done.stderr, encoding="utf-8")
    output = json.loads(out_file.read_text(encoding="utf-8")) if out_file.exists() else {}
    return {"exit_code": done.returncode, "seconds": round(time.perf_counter() - start, 1), "output": output}


def check_run(run, pages, expect):
    """expect: {item_id: expected error or None}. Each item page must show that error; the good ones keep their values."""
    out = run["output"]
    by_path = {p["path"]: p for p in out.get("pages", [])}
    records = {}
    for r in out.get("records", []):
        records.setdefault(r["page"], []).append(r)
    rows = []
    for item, error in expect.items():
        path = pages[item][0]
        seen = by_path.get(path)
        got = None if seen is None else seen.get("error")
        n = len(records.get(path, []))
        ok = seen is not None and got == error and (n == 0 if error else n == len(pages[item][2]))
        rows.append({"item": item, "path": path, "expected_error": error, "error": got, "visited": seen is not None,
                     "records": n, "passed": ok})
    return rows


def write_report(out_dir, report):
    (out_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = ["# Test 7, fake-model part: scraper (c)'s failure rules", "",
             f"Run {report['run_at']} · commit {report['commit']} · fake Ollama on 127.0.0.1:{MODEL_PORT} · "
             f"slow answer after {report['slow_seconds']} s", "", f"**{'PASS' if report['passed'] else 'FAIL'}**", ""]
    for run in report["runs"]:
        lines += [f"## {run['name']}", "",
                  f"Exit {run['exit_code']} · {run['seconds']} s · pages visited {run['pages_visited']} of {run['page_cap']} "
                  f"(cap) · {'finished' if run['exit_code'] == 0 else 'DID NOT FINISH'}", "",
                  "| Page | Fake model's answer | Expected | (c) recorded | Values saved | |", "|---|---|---|---|---|---|"]
        for r in run["rows"]:
            lines.append(f"| {r['path']} | {r.get('answer', '—')} | {r['expected_error'] or 'no error'} | "
                         f"{r['error'] or ('no error' if r['visited'] else 'not visited')} | {r['records']} | "
                         f"{'PASS' if r['passed'] else 'FAIL'} |")
        lines.append("")
    lines += ["Each run's output and printed log are in this folder (`test7-model-*.json`, `.log`).", ""]
    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    from measurement.test4 import generate, git_commit
    from measurement.test6 import start_server
    parser = argparse.ArgumentParser(description="Test 7, fake-model part for scraper (c)")
    parser.add_argument("--out", help="results folder (default results/<today>-test7-model)")
    parser.add_argument("--port", type=int, default=3100, help="port for the test site (default 3100)")
    parser.add_argument("--slow-seconds", type=float, default=125, help="how long the slow answer takes (default 125)")
    args = parser.parse_args()
    if port_in_use(MODEL_PORT):
        raise SystemExit(f"Something is already using port {MODEL_PORT}, probably Ollama. Quit Ollama (its tray icon, "
                         "Quit Ollama), run this test, then start Ollama again.")
    out_dir = Path(args.out) if args.out else ROOT / "results" / f"{datetime.date.today().isoformat()}-test7-model"
    out_dir.mkdir(parents=True, exist_ok=True)
    pages = load_pages()
    generate("baseline")
    server = start_server("baseline", args.port, out_dir / "requests.jsonl")
    calls = []
    try:
        print(f"Run 1: (c) on the whole site with the fake model (one answer takes {args.slow_seconds:g} s) ...", flush=True)
        model = start_fake_model(pages, args.slow_seconds, calls)
        try:
            run1 = run_c(args.port, "test7-model-fake", out_dir, 15)
        finally:
            model.shutdown()
            model.server_close()
        print("Run 2: (c) with no model running ...", flush=True)
        run2 = run_c(args.port, "test7-model-none", out_dir, 4)
    finally:
        server.terminate()
        server.wait(timeout=10)
    expect1 = {item: EXPECTED_ERROR.get(PLAN.get(item)) for item in pages}
    rows1 = check_run(run1, pages, expect1)
    for r in rows1:
        r["answer"] = {"not_json": "not JSON", "list": "a list", "missing_key": "a field missing",
                       "slow": f"after {args.slow_seconds:g} s"}.get(PLAN.get(r["item"]), "good")
    visited2 = [p["path"] for p in run2["output"].get("pages", [])]
    expect2 = {item: "model_error" for item, (path, _, _) in pages.items() if path in visited2}
    rows2 = check_run(run2, pages, expect2)
    for r in rows2:
        r["answer"] = "no model running"
    runs = [
        {"name": "Run 1: fake model, whole site", "page_cap": 15, "exit_code": run1["exit_code"], "seconds": run1["seconds"],
         "pages_visited": len(run1["output"].get("pages", [])), "rows": rows1,
         "passed": run1["exit_code"] == 0 and len(run1["output"].get("pages", [])) == 10 and all(r["passed"] for r in rows1)},
        {"name": "Run 2: no model running, first 4 pages", "page_cap": 4, "exit_code": run2["exit_code"],
         "seconds": run2["seconds"], "pages_visited": len(visited2), "rows": rows2,
         "passed": run2["exit_code"] == 0 and len(visited2) == 4 and bool(rows2) and all(r["passed"] for r in rows2)},
    ]
    (out_dir / "fake-model-calls.json").write_text(json.dumps(calls, indent=2) + "\n", encoding="utf-8")
    report = {"test": "Test 7, fake-model part", "run_at": datetime.datetime.now().isoformat(timespec="seconds"),
              "commit": git_commit(), "slow_seconds": args.slow_seconds, "runs": runs,
              "passed": all(r["passed"] for r in runs)}
    write_report(out_dir, report)
    print()
    print((out_dir / "report.md").read_text(encoding="utf-8"))
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
