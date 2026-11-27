"""False-positive check for the trap defenses (docs/metrics-plan.md, D68; schedule Sun Nov 29).

    python measurement/false_positive.py [--conditions honeypot tarpit] [--sessions 20] [--clicks 6] [--pause 0.5]
                                         [--port 3100] [--out results/<date>-false-positive]

A detection rate means little without its false-positive rate: the honeypot study we compare with (Shy Guys) reports
67.6% of bots caught *at 3% false positives*. So this runs a human-like visitor on each trap site and counts how often
the trap catches it:

  visitor     headless Chromium that starts at the home page and, --clicks times, waits --pause seconds, picks one
              link a person can see (on screen, not hidden by CSS) at random and clicks it. It never reads robots.txt
              and never follows a hidden link, as a person can't. Each session has its own run ID
              (human-<condition>-<n>) and its own seeded random choices, so a rerun repeats the same walks.
  honeypot    a false positive is a session that requested the trap path
  tarpit      the maze entrance is a visible link, so a person can click it: a false positive is a session that
              requested a /maze/ page; it also counts maze pages and seconds spent there

false-positive rate = sessions caught / sessions. Each condition is served with site/server.js on --port with a fresh
request log, kept apart from scraper logs.

Writes report.md, report.json and one request log per condition (<condition>.jsonl). Exits with 1 if the honeypot
catches a visitor (the plan expects 0); the tarpit's rate is reported, not judged, since its link is visible by design.
"""
import argparse
import datetime
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Every link a person could see and click: on screen with a size, and not hidden by CSS.
VISIBLE_LINKS = """() => [...document.querySelectorAll('a[href]')].filter((a) => {
  const r = a.getBoundingClientRect(), s = getComputedStyle(a);
  return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden' && Number(s.opacity) > 0;
}).map((a) => a.getAttribute('href'))"""


def read_log(log_file):
    if not Path(log_file).exists():
        return []
    return [json.loads(x) for x in Path(log_file).read_text(encoding="utf-8").splitlines() if x.strip()]


def walk(browser, port, run_id, rng, clicks, pause):
    """One visitor session: the pages it saw, in order."""
    context = browser.new_context(user_agent=f"Mozilla/5.0 (human-like visitor; run={run_id})")
    page = context.new_page()
    page.goto(f"http://127.0.0.1:{port}/", wait_until="load")
    seen = ["/"]
    for _ in range(clicks):
        page.wait_for_timeout(pause * 1000)
        links = sorted(set(page.evaluate(VISIBLE_LINKS)))
        if not links:
            break
        href = rng.choice(links)
        with page.expect_navigation(wait_until="load", timeout=15000):
            page.locator(f'a[href="{href}"]:visible').first.click()
        seen.append(href)
    context.close()
    return seen


def session_result(entries, run_id, trap_path):
    """What the log says about one session: trap hits, maze pages and seconds on maze pages."""
    mine = sorted((e for e in entries if e.get("run_id") == run_id), key=lambda e: e["timestamp"])
    when = lambda e: datetime.datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
    trap = sum(1 for e in mine if e.get("path") == trap_path or e.get("honeypot_hit"))
    maze_seconds = 0.0
    maze = 0
    for i, e in enumerate(mine):
        if e.get("path", "").startswith("/maze/"):
            maze += 1
            maze_seconds += (when(mine[i + 1]) - when(e)).total_seconds() if i + 1 < len(mine) else e["response_ms"] / 1000
    return {"requests": len(mine), "trap_hits": trap, "maze_pages": maze, "maze_seconds": maze_seconds}


def run_condition(condition, sessions, clicks, pause, port, out_dir, seed, trap_path):
    from playwright.sync_api import sync_playwright
    from measurement.test4 import generate
    from measurement.test6 import start_server
    generate(condition)
    log_file = out_dir / f"{condition}.jsonl"
    log_file.unlink(missing_ok=True)
    walks = []
    server = start_server(condition, port, log_file)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for n in range(1, sessions + 1):
                run_id = f"human-{condition}-{n}"
                walks.append({"run_id": run_id,
                              "pages": walk(browser, port, run_id, random.Random(f"{seed}:{condition}:{n}"), clicks, pause)})
            browser.close()
        time.sleep(0.3)  # the server writes each log line when its response finishes
    finally:
        server.terminate()
        server.wait(timeout=10)
    entries = read_log(log_file)
    for w in walks:
        w.update(session_result(entries, w["run_id"], trap_path))
        w["caught"] = (w["trap_hits"] > 0) if condition == "honeypot" else (w["maze_pages"] > 0)
    caught = sum(w["caught"] for w in walks)
    return {"condition": condition, "sessions": sessions, "caught": caught, "false_positive_rate": caught / sessions,
            "walks": walks}


def write_report(out_dir, report):
    (out_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = ["# False-positive check: a human-like visitor on the trap sites", "",
             f"Run {report['run_at']} · commit {report['commit']} · {report['sessions']} sessions per site · "
             f"{report['clicks']} clicks each · {report['pause']} s pause before each click", "",
             "The visitor clicks only links a person can see, at random, and never reads robots.txt.", "",
             "| Site | Sessions caught | False-positive rate | What catches it | |", "|---|---|---|---|---|"]
    for c in report["conditions"]:
        what = "requested the trap path" if c["condition"] == "honeypot" else "requested a /maze/ page"
        verdict = ("PASS (expected 0)" if c["caught"] == 0 else "FAIL (expected 0)") if c["condition"] == "honeypot" else "reported"
        lines.append(f"| {c['condition']} | {c['caught']} of {c['sessions']} | {100 * c['false_positive_rate']:.0f}% | {what} | {verdict} |")
    for c in report["conditions"]:
        if c["condition"] == "tarpit":
            inside = [w for w in c["walks"] if w["maze_pages"]]
            if inside:
                lines += ["", f"Tarpit: {len(inside)} visitors clicked the visible entrance link. In the maze they loaded "
                          f"{sum(w['maze_pages'] for w in inside) / len(inside):.1f} pages and spent "
                          f"{sum(w['maze_seconds'] for w in inside) / len(inside):.1f} s on average (each maze page "
                          "answers after the tarpit's delay)."]
    lines += ["", "## Each session", "", "| Session | Pages clicked through | Trap hits | Maze pages |", "|---|---|---|---|"]
    for c in report["conditions"]:
        for w in c["walks"]:
            lines.append(f"| `{w['run_id']}` | {' → '.join(w['pages'])} | {w['trap_hits']} | {w['maze_pages']} |")
    lines.append("")
    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    from measurement.test4 import git_commit
    parser = argparse.ArgumentParser(description="False-positive check: a human-like visitor on the trap sites")
    parser.add_argument("--conditions", nargs="+", help="trap sites (default: honeypot, and tarpit if it exists)")
    parser.add_argument("--sessions", type=int, default=20, help="visitor sessions per site (default 20)")
    parser.add_argument("--clicks", type=int, default=6, help="links clicked per session (default 6)")
    parser.add_argument("--pause", type=float, default=0.5, help="seconds before each click (default 0.5)")
    parser.add_argument("--port", type=int, default=3100, help="port for the test server (default 3100)")
    parser.add_argument("--out", help="results folder (default results/<today>-false-positive)")
    args = parser.parse_args()
    conditions = args.conditions or ["honeypot"] + (["tarpit"] if (ROOT / "site" / "defenses" / "tarpit.js").exists() else [])
    out_dir = Path(args.out) if args.out else ROOT / "results" / f"{datetime.date.today().isoformat()}-false-positive"
    out_dir.mkdir(parents=True, exist_ok=True)
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    results = []
    for condition in conditions:
        print(f"{condition}: {args.sessions} visitor sessions of {args.clicks} clicks ...", flush=True)
        results.append(run_condition(condition, args.sessions, args.clicks, args.pause, args.port, out_dir,
                                     config["seed"], config["trap_path"]))
    report = {"check": "false positives on the trap sites", "run_at": datetime.datetime.now().isoformat(timespec="seconds"),
              "commit": git_commit(), "sessions": args.sessions, "clicks": args.clicks, "pause": args.pause,
              "conditions": results}
    write_report(out_dir, report)
    print()
    print((out_dir / "report.md").read_text(encoding="utf-8").split("## Each session")[0])
    honeypot = [c for c in results if c["condition"] == "honeypot"]
    sys.exit(1 if any(c["caught"] for c in honeypot) else 0)


if __name__ == "__main__":
    main()
