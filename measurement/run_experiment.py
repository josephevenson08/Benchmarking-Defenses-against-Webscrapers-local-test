"""Experiment runner (midterm §5 and §7; schedule Wed Nov 18).

    python measurement/run_experiment.py [--scrapers a b] [--conditions baseline shuffled honeypot] [--runs 3]
                                         [--port 3100] [--out results/<date>-experiment]

For each condition, in order:
  1. rebuilds the condition from the data list (same config seed, so the same pages every time),
  2. starts the server on its own port with a fresh request log for that condition,
  3. runs each scraper `--runs` times, one after another, with run IDs like `a-shuffled-2`
     (scraper-condition-number, the form scoring/score.py reads),
  4. stops the server.

Scrapers are found by letter: `scrapers/<letter>_*.py` (for example `a_raw_html.py`), so (c) and (d) join as soon as
their files exist. A run that fails or times out is recorded and the experiment continues.

Writes to the results folder:
  runs/<run-id>.json     each scraper's output
  runs/<run-id>.log      what each scraper printed
  logs/<condition>.jsonl the request log for each condition
  conditions/            the manifest (page list and seeds) of each condition
  manifest.json          what ran, in what order, with exit codes and times, plus the commit, config and tool versions
  summary.md             a quick accuracy check per run (the full results CSV is built separately)
"""

import argparse
import datetime
import json
import platform
import shutil
import subprocess
import sys
import time
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DEFAULT_CONDITIONS = ["baseline", "shuffled", "honeypot"]
OLLAMA_URL = "http://127.0.0.1:11434"


def find_scrapers(scrapers_dir=None):
    """{letter: path} for every scrapers/<letter>_*.py file (letters a to e)."""
    scrapers_dir = Path(scrapers_dir or ROOT / "scrapers")
    found = {}
    for path in sorted(scrapers_dir.glob("[a-e]_*.py")):
        found.setdefault(path.name[0], path)
    return found


def run_id(scraper, condition, n):
    return f"{scraper}-{condition}-{n}"


def plan(scrapers, conditions, runs):
    """Every run in order: condition, then scraper, then run number."""
    return [{"condition": c, "scraper": s, "n": n, "run_id": run_id(s, c, n)}
            for c in conditions for s in scrapers for n in range(1, runs + 1)]


def run_scraper(script, rid, port, out_file, log_file, timeout):
    """Runs one scraper; saves what it printed. Returns exit code (None on timeout) and wall seconds."""
    cmd = [sys.executable, str(script), "--start-url", f"http://127.0.0.1:{port}/", "--run-id", rid, "--out", str(out_file)]
    start = time.perf_counter()
    try:
        done = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        code, printed = done.returncode, done.stdout + done.stderr
    except subprocess.TimeoutExpired as err:
        code = None
        printed = ((err.stdout or b"").decode(errors="replace") if isinstance(err.stdout, bytes) else (err.stdout or "")) \
            + f"\n[runner] stopped after {timeout} s\n"
    wall = round(time.perf_counter() - start, 3)
    log_file.write_text(printed, encoding="utf-8")
    return code, wall


def tool_versions():
    """Versions for the reproducibility manifest (§5). Missing tools are recorded as such."""
    versions = {"python": platform.python_version(), "os": platform.platform()}
    try:
        versions["node"] = subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip()
    except OSError:
        versions["node"] = "not found"
    for package in ("playwright", "requests", "beautifulsoup4"):
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = "not installed"
    return versions


def ollama_info(base_url=OLLAMA_URL):
    """Ollama's version and pulled models with digests, if Ollama is running (needed once (c) runs)."""
    try:
        import requests
        version = requests.get(f"{base_url}/api/version", timeout=3).json().get("version")
        models = [{"name": m.get("name"), "digest": m.get("digest")}
                  for m in requests.get(f"{base_url}/api/tags", timeout=3).json().get("models", [])]
        return {"version": version, "models": models}
    except Exception:  # noqa: BLE001 - Ollama is optional until (c) runs
        return {"version": None, "models": [], "note": "Ollama not reachable"}


def quick_score(out_file):
    """Accuracy from scoring/score.py, as a check (the results CSV comes from the full scoring step)."""
    done = subprocess.run([sys.executable, "scoring/score.py", "--json", str(out_file)], cwd=ROOT, capture_output=True, text=True)
    if done.returncode != 0:
        return None
    s = json.loads(done.stdout)
    return {"correct": s["correct"], "scored_fields": s["scored_fields"], "accuracy": s["accuracy"],
            "pages_fetched": s["pages_fetched"], "time_per_page": s["time_per_page"]}


def write_summary(out_dir, manifest):
    lines = [
        "# Experiment runs",
        "",
        f"Run {manifest['started_at']} → {manifest['finished_at']} · commit {manifest['commit']} · "
        f"scrapers {', '.join(manifest['scrapers'])} · conditions {', '.join(manifest['conditions'])} · {manifest['runs_per_cell']} runs per cell",
        "",
        "| Run ID | Exit | Wall (s) | Accuracy | Pages | Time per page |",
        "|---|---|---|---|---|---|",
    ]
    for r in manifest["runs"]:
        q = r.get("quick_score")
        acc = f"{q['correct']}/{q['scored_fields']} = {q['accuracy']:.3f}" if q else "—"
        pages = q["pages_fetched"] if q else "—"
        tpp = f"{q['time_per_page']:.3f} s" if q else "—"
        exit_code = "timeout" if r["exit_code"] is None else r["exit_code"]
        lines.append(f"| `{r['run_id']}` | {exit_code} | {r['wall_s']} | {acc} | {pages} | {tpp} |")
    failed = [r["run_id"] for r in manifest["runs"] if r["exit_code"] != 0]
    lines += ["", f"**{len(manifest['runs']) - len(failed)} of {len(manifest['runs'])} runs finished.**"
              + (f" Failed: {', '.join(failed)} (see `runs/<run-id>.log`)." if failed else ""), "",
              "Accuracy here is a quick check from `scoring/score.py`. The results CSV (with honeypot hits and time per page "
              "from the request log, and the standard metrics) is built from this folder in a separate step.", ""]
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Run the scrapers on each condition with unique run IDs")
    parser.add_argument("--scrapers", nargs="+", default=["a", "b"], help="scraper letters (default: a b)")
    parser.add_argument("--conditions", nargs="+", default=DEFAULT_CONDITIONS, help="conditions (default: baseline shuffled honeypot)")
    parser.add_argument("--runs", type=int, default=3, help="runs per scraper and condition (default 3)")
    parser.add_argument("--port", type=int, default=3100, help="port for the experiment server (default 3100)")
    parser.add_argument("--timeout", type=float, default=1800, help="seconds before one scraper run is stopped (default 1800)")
    parser.add_argument("--out", help="results folder (default results/<today>-experiment)")
    parser.add_argument("--no-score", action="store_true", help="skip the quick accuracy check")
    args = parser.parse_args()

    from measurement.test4 import generate, git_commit
    from measurement.test6 import start_server

    available = find_scrapers()
    missing = [s for s in args.scrapers if s not in available]
    if missing:
        raise SystemExit(f"No scraper file for: {', '.join(missing)}. Found: "
                         + ", ".join(f"{k} ({v.name})" for k, v in available.items()))
    out_dir = Path(args.out) if args.out else ROOT / "results" / f"{datetime.date.today().isoformat()}-experiment"
    if out_dir.exists() and any(out_dir.iterdir()):
        raise SystemExit(f"{out_dir} already has files. Choose another --out so earlier runs are not mixed in.")
    for sub in ("runs", "logs", "conditions"):
        (out_dir / sub).mkdir(parents=True, exist_ok=True)

    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    runs = plan(args.scrapers, args.conditions, args.runs)
    manifest = {
        "experiment": "scraper runs",
        "started_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "commit": git_commit(),
        "scrapers": {s: available[s].name for s in args.scrapers},
        "conditions": args.conditions,
        "runs_per_cell": args.runs,
        "port": args.port,
        "config": config,
        "versions": tool_versions(),
        "ollama": ollama_info() if any(s in ("c", "e") for s in args.scrapers) else None,
        "runs": [],
    }
    print(f"{len(runs)} runs: {len(args.conditions)} conditions × {len(args.scrapers)} scrapers × {args.runs} runs")

    for condition in args.conditions:
        generate(condition)
        shutil.copy(ROOT / "conditions" / f"{condition}.manifest.json", out_dir / "conditions" / f"{condition}.manifest.json")
        log_file = out_dir / "logs" / f"{condition}.jsonl"
        server = start_server(condition, args.port, log_file)
        try:
            for r in [r for r in runs if r["condition"] == condition]:
                out_file = out_dir / "runs" / f"{r['run_id']}.json"
                print(f"  {r['run_id']} ...", end=" ", flush=True)
                code, wall = run_scraper(available[r["scraper"]], r["run_id"], args.port, out_file,
                                         out_dir / "runs" / f"{r['run_id']}.log", args.timeout)
                entry = {**r, "exit_code": code, "wall_s": wall,
                         "output": f"runs/{r['run_id']}.json" if out_file.exists() else None,
                         "printed": f"runs/{r['run_id']}.log", "request_log": f"logs/{condition}.jsonl"}
                if not args.no_score and code == 0 and out_file.exists():
                    entry["quick_score"] = quick_score(out_file)
                manifest["runs"].append(entry)
                q = entry.get("quick_score")
                print("timeout" if code is None else (f"{q['correct']}/{q['scored_fields']}" if q else f"exit {code}"))
        finally:
            server.terminate()
            server.wait(timeout=10)

    manifest["finished_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    write_summary(out_dir, manifest)
    print()
    print((out_dir / "summary.md").read_text(encoding="utf-8"))
    sys.exit(0 if all(r["exit_code"] == 0 for r in manifest["runs"]) else 1)


if __name__ == "__main__":
    main()
