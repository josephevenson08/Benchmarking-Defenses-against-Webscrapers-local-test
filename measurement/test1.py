"""Test 1: normal workflow (midterm §5, Test 1).

    python measurement/test1.py [--out results/<date>-test1] [--port 3100] [--runs 3] [--min-accuracy 0.9]

1. Generates the baseline, shuffled and honeypot conditions and checks that each
   has 10 pages and 70 scored fields (70 label elements and 70 value elements on
   its item pages, and a manifest that says 70).
2. Serves the baseline on its own port with a fresh request log and runs
   scrapers (a) and (b) three times each (run IDs a-baseline-1..3, b-baseline-1..3).
3. Scores every run with scoring/score.py. Every run must reach at least 90%.

Writes report.md, report.json, every scraper output (runs/) and the request log
(requests.jsonl) to the results folder. Exits with 1 if a check fails.
"""

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from measurement.test4 import field_sequence, generate, git_commit  # noqa: E402
from measurement.test6 import start_server  # noqa: E402

CONDITIONS = ["baseline", "shuffled", "honeypot"]
SCRAPERS = {"a": "scrapers/a_raw_html.py", "b": "scrapers/b_browser_text.py"}


def condition_counts(conditions_dir, condition):
    """Pages and scored fields of one generated condition."""
    conditions_dir = Path(conditions_dir)
    manifest = json.loads((conditions_dir / f"{condition}.manifest.json").read_text(encoding="utf-8"))
    site = conditions_dir / condition
    html_files = sorted(p for p in site.rglob("*.html"))
    labels = values = 0
    for page in manifest["pages"]:
        if page["type"] in ("product", "article"):
            seq = field_sequence((site / page["file"]).read_text(encoding="utf-8"))
            labels += sum(1 for kind, _ in seq if kind == "label")
            values += sum(1 for kind, _ in seq if kind == "value")
    return {
        "condition": condition,
        "html_files": len(html_files),
        "manifest_pages": len(manifest["pages"]),
        "manifest_scored_fields": manifest["scored_fields"],
        "label_elements": labels,
        "value_elements": values,
    }


def counts_ok(c, pages=10, fields=70):
    return (c["html_files"] == pages and c["manifest_pages"] == pages and c["manifest_scored_fields"] == fields
            and c["label_elements"] == fields and c["value_elements"] == fields)


def run_scraper(scraper, run_id, port, out_file):
    run = subprocess.run(
        [sys.executable, SCRAPERS[scraper], "--start-url", f"http://127.0.0.1:{port}/", "--run-id", run_id,
         "--out", str(out_file)],
        cwd=ROOT, capture_output=True, text=True, timeout=300,
    )
    if run.returncode != 0 or not out_file.exists():
        return (run.stdout + run.stderr).strip()[-2000:]
    return None


def score(out_file):
    run = subprocess.run([sys.executable, "scoring/score.py", "--json", str(out_file)],
                         cwd=ROOT, capture_output=True, text=True)
    if run.returncode != 0:
        return {"error": (run.stdout + run.stderr).strip()[-2000:]}
    return json.loads(run.stdout)


def write_report(out_dir, report):
    (out_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    def mark(ok):
        return "PASS" if ok else "FAIL"

    lines = [
        "# Test 1: normal workflow",
        "",
        f"Run {report['run_at']} · commit {report['commit']} · baseline served on port {report['port']}",
        "",
        "## Conditions: 10 pages and 70 scored fields each",
        "",
        "| Condition | HTML pages | Manifest pages | Manifest fields | Label elements | Value elements | |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in report["conditions"]:
        lines.append(f"| {c['condition']} | {c['html_files']} | {c['manifest_pages']} | {c['manifest_scored_fields']} | "
                     f"{c['label_elements']} | {c['value_elements']} | {mark(c['passed'])} |")
    lines += [
        "",
        f"## Runs on baseline: each at least {report['min_accuracy']:.0%} accurate",
        "",
        "| Run | Accuracy | Fake-value rate | Missing | Pages | Seconds | Time per page | |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in report["runs"]:
        if "error" in r:
            lines.append(f"| `{r['run_id']}` | failed | | | | | | FAIL |")
            continue
        s = r["score"]
        lines.append(
            f"| `{r['run_id']}` | {s['correct']}/{s['scored_fields']} = {s['accuracy']:.3f} | "
            f"{s['fakes']}/{s['scored_fields']} | {s['missing']} | {s['pages_fetched']} | {s['seconds']} | "
            f"{s['time_per_page']:.3f} s | {mark(r['passed'])} |"
        )
    lines += ["", f"**Test 1: {mark(report['passed'])}**", "",
              "Scraper outputs: `runs/`. Request log: `requests.jsonl`.", ""]
    for r in report["runs"]:
        if "error" in r:
            lines += [f"Error from `{r['run_id']}`:", "", "```", r["error"], "```", ""]
    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Test 1: normal workflow")
    parser.add_argument("--out", help="results folder (default: results/<today>-test1)")
    parser.add_argument("--port", type=int, default=3100, help="port for the test server (default 3100)")
    parser.add_argument("--runs", type=int, default=3, help="runs per scraper (default 3)")
    parser.add_argument("--min-accuracy", type=float, default=0.9, help="lowest accuracy allowed per run (default 0.9)")
    parser.add_argument("--scrapers", nargs="+", default=["a", "b"], choices=sorted(SCRAPERS))
    args = parser.parse_args()

    out_dir = Path(args.out) if args.out else ROOT / "results" / f"{datetime.date.today().isoformat()}-test1"
    (out_dir / "runs").mkdir(parents=True, exist_ok=True)

    print("1. Generating", ", ".join(CONDITIONS), "and counting pages and fields ...")
    conditions = []
    for condition in CONDITIONS:
        generate(condition)
        counts = condition_counts(ROOT / "conditions", condition)
        counts["passed"] = counts_ok(counts)
        conditions.append(counts)

    log_file = out_dir / "requests.jsonl"
    log_file.unlink(missing_ok=True)
    print(f"2. Serving baseline on port {args.port} and running the scrapers ...")
    runs = []
    server = start_server("baseline", args.port, log_file)
    try:
        for scraper in args.scrapers:
            for n in range(1, args.runs + 1):
                run_id = f"{scraper}-baseline-{n}"
                print("  ", run_id)
                out_file = out_dir / "runs" / f"{run_id}.json"
                error = run_scraper(scraper, run_id, args.port, out_file)
                runs.append({"run_id": run_id, "error": error} if error else {"run_id": run_id, "file": str(out_file)})
    finally:
        server.terminate()
        server.wait(timeout=10)

    print("3. Scoring every run ...")
    for r in runs:
        if "error" in r:
            r["passed"] = False
            continue
        r["score"] = score(Path(r.pop("file")))
        r["passed"] = "error" not in r["score"] and r["score"]["accuracy"] >= args.min_accuracy
        if "error" in r["score"]:
            r["error"] = r["score"]["error"]

    report = {
        "test": "Test 1: normal workflow",
        "run_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "commit": git_commit(),
        "port": args.port,
        "min_accuracy": args.min_accuracy,
        "conditions": conditions,
        "runs": runs,
        "passed": all(c["passed"] for c in conditions) and bool(runs) and all(r["passed"] for r in runs),
    }
    write_report(out_dir, report)
    print()
    print((out_dir / "report.md").read_text(encoding="utf-8"))
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
