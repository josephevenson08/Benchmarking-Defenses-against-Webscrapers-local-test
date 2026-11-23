"""Builds the results CSV from one or more experiment folders (midterm §4 metrics, §5 analysis; D68, D70).

    python scoring/results.py <results folder> [<results folder> ...] --out <folder>

Each input folder is what measurement/run_experiment.py writes: manifest.json, runs/<run-id>.json and
logs/<condition>.jsonl, plus conditions/<condition>.fakes.json for a poisoned condition. Every field is scored with
scoring/score.py, so the matching rules stay in one place (docs/scraper-output.md, D31-D35); a value that equals its
page's fake counts as a fake (and as wrong).

A condition whose manifest names a fakes file (conditions/<condition>.manifest.json, "fakes_file") must have it, so
poisoned runs are never scored without their fakes.

Writes to --out:
  results.csv  one row per run: the midterm's measures (accuracy, fake-value rate, time per page, honeypot hits)
               and the standard ones (recall, precision, F1, complete run), with counts from the request log
  cells.csv    one row per scraper and condition: mean and min-max over the runs, extraction success rate,
               relative reduction against that scraper's baseline, the midterm's verdict, honeypot detection
               and evasion rates
  summary.md   the cells as a table, plus where every number came from

Definitions (docs/metrics-plan.md):
  recall            = correct / 70, the midterm's accuracy (WebCloak's scraping recall)
  precision         = correct / fields that had a value (wrong values count against it, missing ones don't);
                      blank when the run returned no values at all
  F1                = 2PR / (P + R), 0 when the run returned nothing correct
  complete run      = all 70 fields correct; ESR = complete runs / runs (Beyond BeautifulSoup)
  relative reduction = 1 - mean with the defense / mean on baseline, same scraper
  verdict           = "stops" when mean recall < 10% (§4 item 5); "reduces" when the mean falls below the lowest
                      baseline run by more than the baseline spread (§4 Analysis); otherwise "no effect"
  honeypot hits     = trap-path requests carrying the run's ID in the request log (§4 item 4)
  detection rate    = runs with at least one honeypot hit / runs (Shy Guys); evasion rate = 1 - detection rate
  time per page     = crawl seconds / pages fetched, both from the scraper's output (§4 item 4)
  log page requests = page requests in the request log for the run: robots.txt and files with an extension
                      other than .html (favicon, scripts, styles) are not pages (chat-keeper, Turns 121 and 124)

A run whose output file is missing (the scraper crashed) is scored as a run that found nothing, as score.py scores
an empty output, and is marked with its exit code so it is never mistaken for a real 0.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scoring.score import DataList, load_fakes, parse_run_id, score_run  # noqa: E402

CONDITION_ORDER = ["baseline", "shuffled", "honeypot", "poisoned", "tarpit"]
STOPS_BELOW = 0.10

RUN_COLUMNS = [
    "run_id", "scraper", "condition", "run_number", "source", "commit", "exit_code", "output",
    "scored_fields", "correct", "wrong", "fakes", "malformed", "conflicting", "plain_wrong", "missing",
    "accuracy", "recall", "precision", "f1", "complete_run", "fake_value_rate",
    "pages_fetched", "page_errors", "seconds", "time_per_page",
    "log_page_requests", "honeypot_hits", "mean_response_ms",
]
CELL_COLUMNS = [
    "scraper", "condition", "runs", "failed_runs", "correct_per_run",
    "recall_mean", "recall_min", "recall_max", "precision_mean", "f1_mean",
    "esr", "reduction_recall", "reduction_f1", "verdict", "baseline_check",
    "fake_value_rate_mean", "time_per_page_mean", "time_per_page_min", "time_per_page_max",
    "honeypot_hits", "detection_rate", "evasion_rate",
]


def is_page_request(path: str) -> bool:
    """robots.txt and files with an extension other than .html are not pages."""
    if path == "/robots.txt":
        return False
    last = path.rstrip("/").rsplit("/", 1)[-1]
    return "." not in last or last.endswith(".html")


def read_log(path: Path, trap_path: str) -> dict:
    """{run_id: {"pages": n, "hits": n, "ms": [response_ms, ...]}} from one request log."""
    per_run = defaultdict(lambda: {"pages": 0, "hits": 0, "ms": []})
    if not path.exists():
        return per_run
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        entry = per_run[r.get("run_id")]
        if r.get("path") == trap_path or r.get("honeypot_hit"):
            entry["hits"] += 1
        if is_page_request(r.get("path", "")):
            entry["pages"] += 1
            if isinstance(r.get("response_ms"), (int, float)):
                entry["ms"].append(r["response_ms"])
    return per_run


def condition_fakes(folder: Path, condition: str, data: DataList) -> dict:
    """The condition's fakes ({(item_id, field): fake}) from conditions/<condition>.fakes.json; {} when it has none."""
    fakes_file = folder / "conditions" / f"{condition}.fakes.json"
    manifest_file = folder / "conditions" / f"{condition}.manifest.json"
    named = manifest_file.exists() and json.loads(manifest_file.read_text(encoding="utf-8")).get("fakes_file")
    if not fakes_file.exists():
        if named:
            raise ValueError(f"{manifest_file} names a fakes file, but {fakes_file} is missing. Copy it from "
                             f"conditions/{named} or rerun the experiment.")
        return {}
    return load_fakes(json.loads(fakes_file.read_text(encoding="utf-8")), data)


def precision_of(correct: int, answered: int):
    return correct / answered if answered else None


def f1_of(precision, recall: float) -> float:
    if not precision or not recall:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def run_rows(folders, data: DataList, trap_path: str) -> list[dict]:
    rows, seen = [], {}
    for folder in map(Path, folders):
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        logs, fakes = {}, {}
        for run in manifest["runs"]:
            rid = run["run_id"]
            if rid in seen:
                raise ValueError(f"run {rid} is in both {seen[rid]} and {folder}. Pick one folder for each run.")
            seen[rid] = folder
            scraper, condition, number = parse_run_id(rid)
            if condition not in logs:
                logs[condition] = read_log(folder / "logs" / f"{condition}.jsonl", trap_path)
                fakes[condition] = condition_fakes(folder, condition, data)
            out_file = folder / "runs" / f"{rid}.json"
            output = json.loads(out_file.read_text(encoding="utf-8") or "{}") if out_file.exists() else {}
            if not output.get("run"):
                output.setdefault("run", {"run_id": rid})
            s = score_run(output, data, fakes[condition])
            answered = s.correct + s.wrong
            precision = precision_of(s.correct, answered)
            log = logs[condition].get(rid, {"pages": 0, "hits": 0, "ms": []})
            pages = output.get("pages") or []
            rows.append({
                "run_id": rid, "scraper": scraper, "condition": condition, "run_number": number,
                "source": folder.as_posix(), "commit": manifest.get("commit"), "exit_code": run.get("exit_code"),
                "output": "yes" if out_file.exists() else "missing",
                "scored_fields": s.scored_fields, "correct": s.correct, "wrong": s.wrong, "fakes": s.fakes,
                "malformed": s.malformed, "conflicting": s.count("conflict"), "plain_wrong": s.count("wrong"),
                "missing": s.missing, "accuracy": s.accuracy, "recall": s.accuracy, "precision": precision,
                "f1": f1_of(precision, s.accuracy), "complete_run": s.correct == s.scored_fields,
                "fake_value_rate": s.fake_value_rate, "pages_fetched": s.pages_fetched,
                "page_errors": sum(1 for p in pages if p.get("error")), "seconds": s.seconds,
                "time_per_page": s.time_per_page, "log_page_requests": log["pages"], "honeypot_hits": log["hits"],
                "mean_response_ms": mean(log["ms"]) if log["ms"] else None,
            })
    order = {c: i for i, c in enumerate(CONDITION_ORDER)}
    rows.sort(key=lambda r: (r["scraper"], order.get(r["condition"], 99), r["condition"], r["run_number"]))
    return rows


def verdict(defended_mean: float, baseline_recalls: list) -> str:
    """§4: "stops" below 10%; "reduces" below the lowest baseline run by more than the baseline spread."""
    if defended_mean < STOPS_BELOW:
        return "stops"
    lowest = min(baseline_recalls)
    spread = max(baseline_recalls) - lowest
    return "reduces" if defended_mean < lowest - spread else "no effect"


def cell_rows(rows: list[dict]) -> list[dict]:
    cells = defaultdict(list)
    for r in rows:
        cells[(r["scraper"], r["condition"])].append(r)
    out = []
    for (scraper, condition), runs in cells.items():
        recalls = [r["recall"] for r in runs]
        f1s = [r["f1"] for r in runs]
        precisions = [r["precision"] for r in runs if r["precision"] is not None]
        tpps = [r["time_per_page"] for r in runs if r["time_per_page"] is not None]
        base = cells.get((scraper, "baseline"), [])
        base_recalls = [r["recall"] for r in base]
        base_recall = mean(base_recalls) if base else None
        base_f1 = mean(r["f1"] for r in base) if base else None
        hits = [r["honeypot_hits"] for r in runs]
        detection = sum(h > 0 for h in hits) / len(runs)
        if condition == "baseline":
            v = "baseline"
        else:
            v = verdict(mean(recalls), base_recalls) if base else "no baseline"
        out.append({
            "scraper": scraper, "condition": condition, "runs": len(runs),
            "failed_runs": sum(1 for r in runs if r["exit_code"] != 0 or r["output"] != "yes"),
            "correct_per_run": " ".join(str(r["correct"]) for r in runs),
            "recall_mean": mean(recalls), "recall_min": min(recalls), "recall_max": max(recalls),
            "precision_mean": mean(precisions) if precisions else None, "f1_mean": mean(f1s),
            "esr": sum(r["complete_run"] for r in runs) / len(runs),
            "reduction_recall": None if condition == "baseline" or not base_recall else 1 - mean(recalls) / base_recall,
            "reduction_f1": None if condition == "baseline" or not base_f1 else 1 - mean(f1s) / base_f1,
            "verdict": v,
            "baseline_check": ("pass" if base and min(base_recalls) >= 0.90 else "fail") if base else "no baseline",
            "fake_value_rate_mean": mean(r["fake_value_rate"] for r in runs),
            "time_per_page_mean": mean(tpps) if tpps else None,
            "time_per_page_min": min(tpps) if tpps else None, "time_per_page_max": max(tpps) if tpps else None,
            "honeypot_hits": sum(hits), "detection_rate": detection, "evasion_rate": 1 - detection,
        })
    order = {c: i for i, c in enumerate(CONDITION_ORDER)}
    out.sort(key=lambda c: (c["scraper"], order.get(c["condition"], 99), c["condition"]))
    return out


def write_csv(path: Path, columns: list, rows: list) -> None:
    def cell(v):
        if v is None:
            return ""
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, float):
            return f"{v:.6g}"
        return v
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(columns)
        for r in rows:
            w.writerow([cell(r.get(c)) for c in columns])


def write_summary(path: Path, folders, rows: list, cells: list) -> None:
    def pct(v):
        return "—" if v is None else f"{v * 100:.1f}%"

    def num(v, d=3):
        return "—" if v is None else f"{v:.{d}f}"

    lines = ["# Results", "",
             f"{len(rows)} runs from: " + ", ".join(f"`{Path(f).as_posix()}`" for f in folders) + ".",
             "Definitions: `scoring/results.py` and `docs/metrics-plan.md`.", "",
             "| Scraper | Condition | Correct per run | Recall (min–max) | Precision | F1 | ESR | Reduction | Verdict | "
             "Honeypot detection | Time per page |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in cells:
        rng = "" if c["recall_min"] == c["recall_max"] else f" ({pct(c['recall_min'])}–{pct(c['recall_max'])})"
        lines.append(
            f"| ({c['scraper']}) | {c['condition']} | {c['correct_per_run']} | {pct(c['recall_mean'])}{rng} | "
            f"{num(c['precision_mean'])} | {num(c['f1_mean'])} | {num(c['esr'], 2)} | {pct(c['reduction_recall'])} | "
            f"{c['verdict']} | {num(c['detection_rate'], 2)} | "
            f"{'—' if c['time_per_page_mean'] is None else num(c['time_per_page_mean']) + ' s'} |")
    poisoned = [c for c in cells if c["condition"] == "poisoned"]
    if poisoned:
        lines += ["", "Poisoned site (a fake also counts as wrong): fakes and other wrong values per run.", "",
                  "| Scraper | Fakes per run | Fake-value rate | Other wrong per run | Missing per run |", "|---|---|---|---|---|"]
        for c in poisoned:
            runs = [r for r in rows if r["scraper"] == c["scraper"] and r["condition"] == "poisoned"]
            lines.append(f"| ({c['scraper']}) | {' '.join(str(r['fakes']) for r in runs)} | {pct(c['fake_value_rate_mean'])} | "
                         f"{' '.join(str(r['wrong'] - r['fakes']) for r in runs)} | {' '.join(str(r['missing']) for r in runs)} |")
    failed = [r["run_id"] for r in rows if r["exit_code"] != 0 or r["output"] != "yes"]
    mismatched = [r["run_id"] for r in rows if r["output"] == "yes" and r["log_page_requests"] != r["pages_fetched"]]
    lines += ["", f"Failed runs (scored as finding nothing): {', '.join(failed) if failed else 'none'}.",
              f"Runs whose request log shows a different page count from their output: "
              f"{', '.join(mismatched) if mismatched else 'none'}.", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build the results CSV from experiment folders.")
    parser.add_argument("folders", nargs="+", help="results folders written by measurement/run_experiment.py")
    parser.add_argument("--out", required=True, help="folder for results.csv, cells.csv and summary.md")
    args = parser.parse_args(argv)
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    try:
        rows = run_rows(args.folders, DataList.load(), config["trap_path"])
    except (OSError, ValueError, KeyError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    cells = cell_rows(rows)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "results.csv", RUN_COLUMNS, rows)
    write_csv(out / "cells.csv", CELL_COLUMNS, cells)
    write_summary(out / "summary.md", args.folders, rows, cells)
    print((out / "summary.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
