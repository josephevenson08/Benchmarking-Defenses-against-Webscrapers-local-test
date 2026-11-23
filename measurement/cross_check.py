"""Cross-check of the results (D102): recounts everything from the raw files, without scoring/score.py,
scoring/results.py or measurement/user_cost.py, and compares with what those scripts reported.

    python measurement/cross_check.py --runs <runner folder> [<runner folder> ...] --results <results folder>
                                      [--cost <user-cost folder>] [--out results/<date>-cross-check]

Scraping (each run, from runs/<id>.json, logs/<condition>.jsonl and conditions/<condition>.manifest.json):
  - the matching rules of docs/scraper-output.md, written again here from the document: correct, wrong
    (including malformed and conflicting) and missing fields out of 70;
  - honeypot hits (requests for the trap path with the run's ID), page requests, time per page;
  - precision, F1, complete run; then for each scraper and condition the mean and min-max recall, extraction
    success rate, drop in recall and the midterm's verdict (stops < 10%; reduces = below the lowest baseline run
    by more than the baseline spread), and the detection rate;
  - that every log line of a condition belongs to a run of that condition, that each output's run ID and scraper
    match its file name, and that every folder used the same pages and seeds for each condition.
  The independent counter is first run on the Test 2 fixture, which Joseph worked out by hand (63 correct,
  4 wrong, 3 missing, 2 fakes).

User cost (with --cost):
  - HTML size, from a fresh copy of each condition generated into a temporary folder;
  - pixel difference, by comparing the saved screenshots pixel by pixel;
  - reading order, from each page's HTML and its CSS order values (no browser);
  - axe-core violations, from the saved axe reports;
  - Lighthouse, the medians and changes recomputed from every saved run.

Writes report.md (every check, and the tally for each scraper and condition) and exits with 1 if any check fails.
"""

import argparse
import csv
import datetime
import json
import re
import statistics
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
NUM = re.compile(r"\d+(\.\d+)?")
TOL = 1e-6  # absolute; the CSVs store 6 significant digits, so a relative 1e-5 is allowed as well


# ---------- matching rules, written again from docs/scraper-output.md ----------

def blank(v):
    return v is None or "".join(str(v).split()) == ""


def comparable(field, v):
    """The value in the form the rules compare, or ('malformed', text)."""
    s = " ".join(str(v).split())
    if field == "price":
        t = s.replace("$", "").replace(",", "").strip()
        return round(float(t) * 100) if NUM.fullmatch(t) else ("malformed", s)
    if field == "rating":
        return float(s) if NUM.fullmatch(s) else ("malformed", s)
    if field == "review_count":
        t = s.replace(",", "")
        return int(float(t)) if NUM.fullmatch(t) and float(t).is_integer() else ("malformed", s)
    if field in ("release_date", "publish_date"):
        return s
    if field == "tags":
        return frozenset(x.strip().lower() for x in s.split(",") if x.strip())
    return s.lower()


def load_truth():
    items = json.loads((ROOT / "data" / "items.json").read_text(encoding="utf-8"))
    fields = json.loads((ROOT / "data" / "fields.json").read_text(encoding="utf-8"))
    truth = {}
    for kind, idkey, fkind in (("products", "product_id", "product"), ("articles", "article_id", "article")):
        for item in items[kind]:
            for f in fields[fkind]:
                truth[(item[idkey], f["key"])] = item[f["key"]]
    return truth


def clean_path(page):
    path = urlparse(str(page or "")).path
    if path.endswith(".html"):
        path = path[:-5]
    return path.rstrip("/") or "/"


def recount(output, truth, page_items, fakes=None):
    """{'correct', 'wrong', 'missing', 'fakes', 'malformed', 'conflict'} for one output, out of len(truth)."""
    fakes = fakes or {}
    seen = defaultdict(list)
    for r in output.get("records") or []:
        item = page_items.get(clean_path(r.get("page")))
        if (item, r.get("field")) in truth and not blank(r.get("value")):
            seen[(item, r["field"])].append(r["value"])
    tally = dict.fromkeys(("correct", "wrong", "missing", "fakes", "malformed", "conflict"), 0)
    for (item, field), real in truth.items():
        values = seen.get((item, field), [])
        if not values:
            tally["missing"] += 1
            continue
        forms = {comparable(field, v) for v in values}
        if len(forms) > 1:
            tally["wrong"] += 1
            tally["conflict"] += 1
            continue
        form = forms.pop()
        if isinstance(form, tuple):
            tally["wrong"] += 1
            tally["malformed"] += 1
        elif form == comparable(field, real):
            tally["correct"] += 1
        else:
            tally["wrong"] += 1
            if (item, field) in fakes and form == comparable(field, fakes[(item, field)]):
                tally["fakes"] += 1
    return tally


# ---------- scraping runs ----------

class Checks:
    def __init__(self):
        self.items = []

    def add(self, name, ok, detail=""):
        self.items.append((name, bool(ok), detail))
        return ok

    def close(self, name, a, b, detail=""):
        same = (a is None and b is None) or (a is not None and b is not None and
                                              abs(float(a) - float(b)) <= max(TOL, 1e-5 * abs(float(b))))
        return self.add(name, same, detail or f"recounted {a}, reported {b}")


def number(v):
    return None if v in ("", None) else float(v)


def is_page(path):
    last = path.rstrip("/").rsplit("/", 1)[-1]
    return path != "/robots.txt" and ("." not in last or last.endswith(".html"))


def check_runs(folders, results_dir, checks, trap):
    truth = load_truth()
    reported = {r["run_id"]: r for r in csv.DictReader(open(Path(results_dir) / "results.csv", encoding="utf-8"))}
    reported_cells = {(r["scraper"], r["condition"]): r for r in csv.DictReader(open(Path(results_dir) / "cells.csv", encoding="utf-8"))}
    manifests = defaultdict(dict)
    runs = []
    for folder in map(Path, folders):
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        for cond_file in sorted((folder / "conditions").glob("*.manifest.json")):
            manifests[cond_file.name][folder.as_posix()] = json.loads(cond_file.read_text(encoding="utf-8"))
        logs = {}
        for run in manifest["runs"]:
            rid = run["run_id"]
            scraper, condition, n = rid.split("-")[0], rid.split("-")[1], int(rid.split("-")[2])
            if condition not in logs:
                lines = [json.loads(x) for x in (folder / "logs" / f"{condition}.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
                logs[condition] = lines
                strays = [x["run_id"] for x in lines if x.get("run_id", "").split("-")[1:2] != [condition]]
                checks.add(f"{folder.name} logs/{condition}.jsonl: every request is from a {condition} run", not strays,
                           f"{len(lines)} requests" + (f"; others: {sorted(set(strays))}" if strays else ""))
            out_file = folder / "runs" / f"{rid}.json"
            output = json.loads(out_file.read_text(encoding="utf-8")) if out_file.exists() else {}
            run_block = output.get("run", {})
            checks.add(f"{rid}: output names the right run and scraper",
                       run_block.get("run_id") == rid and run_block.get("scraper") == scraper,
                       f"run_id {run_block.get('run_id')}, scraper {run_block.get('scraper')}")
            page_items = {clean_path(p["path"]): p["item_id"] for p in
                          json.loads((folder / "conditions" / f"{condition}.manifest.json").read_text(encoding="utf-8"))["pages"]
                          if p.get("item_id")}
            fakes_file = folder / "conditions" / f"{condition}.fakes.json"
            fakes = {(f["item_id"], f["field"]): f["fake_value"] for f in json.loads(fakes_file.read_text(encoding="utf-8"))} \
                if fakes_file.exists() else {}
            t = recount(output, truth, page_items, fakes)
            mine = [x for x in logs[condition] if x.get("run_id") == rid]
            hits = sum(1 for x in mine if x.get("path") == trap)
            log_pages = sum(1 for x in mine if is_page(x.get("path", "")))
            agents_ok = all(rid in str(x.get("user_agent", "")) for x in mine)
            pages = len(output.get("pages") or [])
            seconds = run_block.get("seconds")
            answered = t["correct"] + t["wrong"]
            precision = t["correct"] / answered if answered else None
            recall = t["correct"] / len(truth)
            f1 = 2 * precision * recall / (precision + recall) if precision and recall else 0.0
            row = {"run_id": rid, "scraper": scraper, "condition": condition, "n": n, "recall": recall, "precision": precision,
                   "f1": f1, "complete": t["correct"] == len(truth), "hits": hits,
                   "tpp": seconds / pages if pages and seconds is not None else None, **t}
            runs.append(row)
            rep = reported.get(rid)
            if not checks.add(f"{rid}: in results.csv", rep is not None):
                continue
            checks.add(f"{rid}: correct / wrong / missing", (t["correct"], t["wrong"], t["missing"]) ==
                       (int(rep["correct"]), int(rep["wrong"]), int(rep["missing"])),
                       f"recounted {t['correct']}/{t['wrong']}/{t['missing']}, reported {rep['correct']}/{rep['wrong']}/{rep['missing']}")
            checks.close(f"{rid}: precision", precision, number(rep["precision"]))
            checks.close(f"{rid}: F1", f1, number(rep["f1"]))
            checks.add(f"{rid}: honeypot hits", hits == int(rep["honeypot_hits"]), f"recounted {hits}, reported {rep['honeypot_hits']}")
            if fakes:
                checks.add(f"{rid}: fakes", t["fakes"] == int(rep["fakes"]), f"recounted {t['fakes']}, reported {rep['fakes']}")
            checks.add(f"{rid}: pages in output = page requests in log", pages == log_pages == int(rep["log_page_requests"]),
                       f"output {pages}, log {log_pages}, reported {rep['log_page_requests']}")
            checks.add(f"{rid}: every request carries the run ID", agents_ok and bool(mine), f"{len(mine)} requests")
            checks.close(f"{rid}: time per page", row["tpp"], number(rep["time_per_page"]))
    for name, by_folder in manifests.items():
        versions = {json.dumps(m, sort_keys=True) for m in by_folder.values()}
        checks.add(f"same pages and seeds for {name} in every folder", len(versions) == 1, f"{len(by_folder)} folders")

    cells = defaultdict(list)
    for r in runs:
        cells[(r["scraper"], r["condition"])].append(r)
    tally = []
    order = ["baseline", "shuffled", "honeypot", "poisoned", "tarpit"]
    for (scraper, condition), rs in sorted(cells.items(), key=lambda kv: (kv[0][0], order.index(kv[0][1]) if kv[0][1] in order else 99, kv[0][1])):
        rs.sort(key=lambda r: r["n"])
        recalls = [r["recall"] for r in rs]
        base = [r["recall"] for r in cells.get((scraper, "baseline"), [])]
        mean = statistics.mean(recalls)
        if condition == "baseline":
            verdict, drop = "baseline", None
        else:
            drop = 1 - mean / statistics.mean(base)
            verdict = "stops" if mean < 0.10 else ("reduces" if mean < min(base) - (max(base) - min(base)) else "no effect")
        esr = sum(r["complete"] for r in rs) / len(rs)
        detection = sum(r["hits"] > 0 for r in rs) / len(rs)
        precisions = [r["precision"] for r in rs if r["precision"] is not None]
        rep = reported_cells.get((scraper, condition))
        name = f"({scraper}) on {condition}"
        if checks.add(f"{name}: in cells.csv", rep is not None):
            checks.add(f"{name}: correct per run", " ".join(str(r["correct"]) for r in rs) == rep["correct_per_run"],
                       f"recounted {[r['correct'] for r in rs]}, reported {rep['correct_per_run']}")
            checks.close(f"{name}: mean recall", mean, number(rep["recall_mean"]))
            checks.close(f"{name}: min recall", min(recalls), number(rep["recall_min"]))
            checks.close(f"{name}: max recall", max(recalls), number(rep["recall_max"]))
            checks.close(f"{name}: mean precision", statistics.mean(precisions) if precisions else None, number(rep["precision_mean"]))
            checks.close(f"{name}: mean F1", statistics.mean(r["f1"] for r in rs), number(rep["f1_mean"]))
            checks.close(f"{name}: success rate", esr, number(rep["esr"]))
            checks.close(f"{name}: drop in recall", drop, number(rep["reduction_recall"]))
            checks.add(f"{name}: verdict", verdict == rep["verdict"], f"recounted {verdict}, reported {rep['verdict']}")
            checks.close(f"{name}: detection rate", detection, number(rep["detection_rate"]))
        tally.append({"cell": name, "per_run": [r["correct"] for r in rs], "wrong": [r["wrong"] for r in rs],
                      "fakes": [r["fakes"] for r in rs],
                      "missing": [r["missing"] for r in rs], "hits": [r["hits"] for r in rs], "verdict": verdict,
                      "drop": drop, "detection": detection})
    return tally


def check_fixture(checks):
    """The independent counter on the Test 2 fixture, against Joseph's hand count."""
    truth = load_truth()
    fixture = ROOT / "scoring" / "fixtures" / "test2"
    output = json.loads((fixture / "output.json").read_text(encoding="utf-8"))
    fakes = {(f["item_id"], f["field"]): f["fake_value"] for f in json.loads((fixture / "fakes.json").read_text(encoding="utf-8"))}
    pages = {f"/{kind}/{item}": item for (item, _) in truth for kind in ("products", "articles")}
    t = recount(output, truth, pages, fakes)
    checks.add("independent counter on the Test 2 fixture: 63 correct, 4 wrong (2 fakes, 1 malformed), 3 missing",
               (t["correct"], t["wrong"], t["missing"], t["fakes"], t["malformed"]) == (63, 4, 3, 2, 1),
               f"got {t['correct']} correct, {t['wrong']} wrong ({t['fakes']} fakes, {t['malformed']} malformed), {t['missing']} missing")


# ---------- user cost ----------

FIELD_SPAN = re.compile(r'<span class="(label|value)"(?: style="order: (\d+)")?>(.*?)</span>', re.S)


def html_fields(html):
    """[(kind, text, css order)] of the fields block, in source order."""
    block = html.split('<div class="fields">', 1)[1].split("</main>", 1)[0] if '<div class="fields">' in html else ""
    return [(k, " ".join(t.split()), int(o) if o else 0) for k, o, t in FIELD_SPAN.findall(block)]


def swapped(fields, values):
    """A poisoned page's fields as the browser shows them after the swap: each value gets the real value for its label
    from the page's real-values JSON ({"fields": [{label, value}]}); other elements stay as they are."""
    real = {" ".join(f["label"].split()): " ".join(str(f["value"]).split()) for f in values["fields"]}
    out, label = [], None
    for kind, text, order in fields:
        if kind == "value" and label in real:
            text = real[label]
        label = text if kind == "label" else None
        out.append((kind, text, order))
    return out


def out_of_order(base, other):
    """Fields whose label or value sits at a different place in the source than on screen (stable sort by order)."""
    pairs = [(base[i][1], base[i + 1][1]) for i in range(len(base) - 1) if base[i][0] == "label" and base[i + 1][0] == "value"]
    screen = [x[:2] for x in sorted(other, key=lambda x: x[2])]
    source = [x[:2] for x in other]
    count = 0
    for label, value in pairs:
        for key in (("label", label), ("value", value)):
            if key not in source or source.index(key) != screen.index(key):
                count += 1
                break
    return len(pairs), count


def check_cost(cost_dir, checks):
    from PIL import Image, ImageChops
    cost_dir = Path(cost_dir)
    pages_rows = list(csv.DictReader(open(cost_dir / "pages.csv", encoding="utf-8")))
    cost_rows = {r["condition"]: r for r in csv.DictReader(open(cost_dir / "cost.csv", encoding="utf-8"))}
    conditions = list(cost_rows)
    with tempfile.TemporaryDirectory() as tmp:
        sizes, fields = {}, {}
        for cond in conditions:
            subprocess.run(["node", str(ROOT / "site" / "generate.js"), cond, "--out", tmp], cwd=ROOT, check=True, capture_output=True)
            manifest = json.loads(Path(tmp, f"{cond}.manifest.json").read_text(encoding="utf-8"))
            for p in manifest["pages"]:
                html = Path(tmp, cond, p["file"]).read_text(encoding="utf-8")
                sizes[(cond, p["path"])] = Path(tmp, cond, p["file"]).stat().st_size
                fields[(cond, p["path"])] = html_fields(html)
                if p.get("values"):  # poisoned: compare what the page shows after its swap, as the screenshots do
                    values = json.loads(Path(tmp, cond, p["values"].lstrip("/")).read_text(encoding="utf-8"))
                    fields[(cond, p["path"])] = swapped(fields[(cond, p["path"])], values)
    for r in pages_rows:
        key = (r["condition"], r["page"])
        checks.add(f"user cost {r['condition']} {r['page']}: HTML bytes", sizes.get(key) == int(r["html_bytes"]),
                   f"regenerated {sizes.get(key)}, reported {r['html_bytes']}")
        n, out = out_of_order(fields[("baseline", r["page"])], fields[key])
        checks.add(f"user cost {r['condition']} {r['page']}: fields out of reading order", (n, out) == (int(r["fields"]), int(r["fields_out_of_order"])),
                   f"from the HTML {out}/{n}, reported {r['fields_out_of_order']}/{r['fields']}")
    for cond in conditions:
        if cond == "baseline":
            continue
        shots = sorted((cost_dir / "screenshots" / "baseline").glob("*.png"))
        differing = 0
        for shot in shots:
            a = Image.open(shot).convert("RGB")
            b = Image.open(cost_dir / "screenshots" / cond / shot.name).convert("RGB")
            differing += (a.size != b.size) or (ImageChops.difference(a, b).getbbox() is not None)
        reported_max = number(cost_rows[cond]["pixel_diff_max_percent"])
        checks.add(f"user cost {cond}: screenshots identical to baseline pixel for pixel when 0% is reported",
                   (differing == 0) == (reported_max == 0), f"{differing} of {len(shots)} pages differ; reported max {reported_max}%")
        if number(cost_rows[cond].get("pages_with_fakes")):
            config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
            manifest = json.loads((cost_dir / "manifest.json").read_text(encoding="utf-8"))
            low, high = config["poison_swap_delay_seconds"], manifest["wait_seconds"]
            longest = number(cost_rows[cond]["fakes_visible_max_s"])
            checks.add(f"user cost {cond}: fakes stay on screen at least the swap delay and end before the screenshot",
                       longest is not None and low <= longest < high, f"longest {longest} s; swap delay {low} s, screenshot at {high} s")
        axe = json.loads((cost_dir / f"axe-{cond}.json").read_text(encoding="utf-8")) if (cost_dir / f"axe-{cond}.json").exists() else None
        if axe is not None:
            count = sum(v["nodes"] for page in axe.values() for v in page)
            checks.add(f"user cost {cond}: axe-core violations", count == int(float(cost_rows[cond]["axe_violations"])),
                       f"from the axe report {count}, reported {cost_rows[cond]['axe_violations']}")
        lh_file, base_file = cost_dir / f"lighthouse-{cond}.json", cost_dir / "lighthouse-baseline.json"
        if lh_file.exists() and base_file.exists():
            lh, base = json.loads(lh_file.read_text(encoding="utf-8")), json.loads(base_file.read_text(encoding="utf-8"))
            base_by = {p["path"]: p for p in base["pages"]}
            for k in ("score", "fcp_ms", "lcp_ms", "tti_ms"):
                changes = [statistics.median(r[k] for r in p["runs"]) - statistics.median(r[k] for r in base_by[p["path"]]["runs"])
                           for p in lh["pages"]]
                checks.close(f"user cost {cond}: Lighthouse {k} change (median of runs, mean over pages)",
                             statistics.mean(changes), number(cost_rows[cond][f"lh_{k}_change_mean"]))


def write_report(out_dir, checks, tally, args):
    failed = [c for c in checks.items if not c[1]]
    lines = ["# Cross-check of the results", "",
             f"Run {datetime.datetime.now().isoformat(timespec='seconds')} · runs: {', '.join(f'`{f}`' for f in args.runs)} · "
             f"results: `{args.results}`" + (f" · user cost: `{args.cost}`" if args.cost else ""), "",
             f"**{len(checks.items) - len(failed)} of {len(checks.items)} checks agree.**" +
             ("" if not failed else f" **{len(failed)} disagree** (listed first)."), "",
             "## Tally for each scraper and defense (recounted from the raw outputs and logs)", "",
             "| Scraper and site | Correct per run (of 70) | Wrong | of which fakes | Missing | Trap hits | Drop in recall | Verdict | Detection |",
             "|---|---|---|---|---|---|---|---|---|"]
    for t in tally:
        drop = "—" if t["drop"] is None else f"{100 * t['drop']:.1f}%"
        lines.append(f"| {t['cell']} | {' '.join(map(str, t['per_run']))} | {' '.join(map(str, t['wrong']))} | "
                     f"{' '.join(map(str, t['fakes']))} | "
                     f"{' '.join(map(str, t['missing']))} | {' '.join(map(str, t['hits']))} | {drop} | {t['verdict']} | {t['detection']:.2f} |")
    lines += ["", "## Every check", "", "| Check | Agrees | Detail |", "|---|---|---|"]
    for name, ok, detail in sorted(checks.items, key=lambda c: c[1]):
        lines.append(f"| {name} | {'yes' if ok else '**NO**'} | {detail} |")
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return failed


def main():
    parser = argparse.ArgumentParser(description="Recount the results from the raw files and compare")
    parser.add_argument("--runs", nargs="+", required=True, help="runner folders (as given to scoring/results.py)")
    parser.add_argument("--results", required=True, help="folder with results.csv and cells.csv from scoring/results.py")
    parser.add_argument("--cost", help="user-cost folder from measurement/user_cost.py")
    parser.add_argument("--out", help="output folder (default results/<today>-cross-check)")
    args = parser.parse_args()
    trap = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))["trap_path"]
    checks = Checks()
    check_fixture(checks)
    tally = check_runs(args.runs, args.results, checks, trap)
    if args.cost:
        check_cost(args.cost, checks)
    out = Path(args.out) if args.out else ROOT / "results" / f"{datetime.date.today().isoformat()}-cross-check"
    out.mkdir(parents=True, exist_ok=True)
    failed = write_report(out, checks, tally, args)
    print(f"{len(checks.items) - len(failed)} of {len(checks.items)} checks agree. Report: {out / 'report.md'}")
    for name, _, detail in failed:
        print("  DISAGREES:", name, "-", detail)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
