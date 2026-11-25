"""Tests for scoring/results.py, on small made-up experiment folders. Run from the repository root:

    python -m unittest discover -s scoring/tests -t .
"""
import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from scoring import results as rs
from scoring.score import DataList

ROOT = Path(__file__).resolve().parents[2]
DATA = DataList.load()
TEST2_OUTPUT = json.loads((ROOT / "scoring" / "fixtures" / "test2" / "output.json").read_text(encoding="utf-8"))
PAGE_OF = {item_id: path for path, item_id in DATA.pages.items()}


def output(run_id, correct=70, seconds=1.0, pages=10):
    """A scraper output with `correct` right values; the rest are left out (missing)."""
    records = [{"page": PAGE_OF[item], "field": f, "value": v} for (item, f), v in list(DATA.truth.items())[:correct]]
    return {"run": {"run_id": run_id, "seconds": seconds},
            "pages": [{"path": f"/p{i}", "status": 200, "error": None} for i in range(pages)], "records": records}


def log_lines(run_id, pages=10, trap=False, extra=()):
    lines = [{"run_id": run_id, "path": "/robots.txt", "response_ms": 1.0, "honeypot_hit": False}]
    lines += [{"run_id": run_id, "path": f"/products/p{i}", "response_ms": 2.0, "honeypot_hit": False} for i in range(pages)]
    lines += [{"run_id": run_id, "path": p, "response_ms": 1.0, "honeypot_hit": False} for p in extra]
    if trap:
        lines.append({"run_id": run_id, "path": "/trap", "response_ms": 1.0, "honeypot_hit": True})
    return lines


def make_folder(tmp, name, runs, logs):
    """runs: {run_id: (output dict or None, exit_code)}; logs: {condition: [log line dicts]}."""
    folder = Path(tmp, name)
    (folder / "runs").mkdir(parents=True)
    (folder / "logs").mkdir()
    manifest = {"commit": "abc1234", "runs": []}
    for rid, (out, code) in runs.items():
        manifest["runs"].append({"run_id": rid, "exit_code": code})
        if out is not None:
            (folder / "runs" / f"{rid}.json").write_text(json.dumps(out), encoding="utf-8")
    (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    for cond, lines in logs.items():
        (folder / "logs" / f"{cond}.jsonl").write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
    return folder


class PageRequestTest(unittest.TestCase):
    def test_only_pages_count(self):
        for path in ("/", "/products/", "/products/p1", "/products/p1.html", "/trap"):
            self.assertTrue(rs.is_page_request(path), path)
        for path in ("/robots.txt", "/favicon.ico", "/shuffle.css", "/assets/app.js"):
            self.assertFalse(rs.is_page_request(path), path)

    def test_log_counts_pages_and_trap_hits_per_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "honeypot.jsonl")
            lines = log_lines("a-honeypot-1", trap=True, extra=["/favicon.ico"]) + log_lines("a-honeypot-2")
            path.write_text("\n".join(json.dumps(x) for x in lines), encoding="utf-8")
            per_run = rs.read_log(path, "/trap")
        self.assertEqual((per_run["a-honeypot-1"]["pages"], per_run["a-honeypot-1"]["hits"]), (11, 1))
        self.assertEqual((per_run["a-honeypot-2"]["pages"], per_run["a-honeypot-2"]["hits"]), (10, 0))


class StandardMetricsTest(unittest.TestCase):
    def test_precision_and_f1_on_the_test2_fixture(self):
        # Test 2: 63 correct, 4 wrong, 3 missing. Without the fakes file the 2 fakes are plain wrong, still wrong.
        with tempfile.TemporaryDirectory() as tmp:
            folder = make_folder(tmp, "x", {"a-baseline-1": (TEST2_OUTPUT, 0)}, {"baseline": log_lines("a-baseline-1")})
            [row] = rs.run_rows([folder], DATA, "/trap")
        self.assertEqual((row["correct"], row["wrong"], row["missing"]), (63, 4, 3))
        self.assertAlmostEqual(row["recall"], 0.9)
        self.assertAlmostEqual(row["precision"], 63 / 67)
        p, r = 63 / 67, 0.9
        self.assertAlmostEqual(row["f1"], 2 * p * r / (p + r))
        self.assertFalse(row["complete_run"])

    def test_nothing_returned_has_no_precision_and_f1_zero(self):
        self.assertIsNone(rs.precision_of(0, 0))
        self.assertEqual(rs.f1_of(None, 0.0), 0.0)
        self.assertEqual(rs.f1_of(0.0, 0.0), 0.0)


class VerdictTest(unittest.TestCase):
    def test_stops_below_ten_percent(self):
        self.assertEqual(rs.verdict(4 / 70, [1.0, 1.0, 1.0]), "stops")
        self.assertEqual(rs.verdict(7 / 70, [1.0, 1.0, 1.0]), "reduces")

    def test_reduces_needs_more_than_the_baseline_spread(self):
        base = [1.0, 0.9, 0.95]  # lowest 0.9, spread 0.1: "reduces" needs a mean below 0.8
        self.assertEqual(rs.verdict(0.85, base), "no effect")
        self.assertEqual(rs.verdict(0.75, base), "reduces")
        self.assertEqual(rs.verdict(69 / 70, [1.0, 1.0, 1.0]), "reduces")
        self.assertEqual(rs.verdict(1.0, [1.0, 1.0, 1.0]), "no effect")


class FoldersTest(unittest.TestCase):
    def build(self, tmp):
        runs = {}
        logs = {"baseline": [], "shuffled": [], "honeypot": []}
        for n in (1, 2, 3):
            runs[f"a-baseline-{n}"] = (output(f"a-baseline-{n}"), 0)
            logs["baseline"] += log_lines(f"a-baseline-{n}")
            runs[f"a-shuffled-{n}"] = (output(f"a-shuffled-{n}", correct=35), 0)
            logs["shuffled"] += log_lines(f"a-shuffled-{n}")
            runs[f"a-honeypot-{n}"] = (output(f"a-honeypot-{n}", pages=11), 0)
            logs["honeypot"] += log_lines(f"a-honeypot-{n}", trap=n != 3)
        runs["a-honeypot-3"] = (None, 1)  # crashed: no output file
        return make_folder(tmp, "exp", runs, logs)

    def test_cells_have_esr_reduction_verdict_and_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = rs.run_rows([self.build(tmp)], DATA, "/trap")
        cells = {c["condition"]: c for c in rs.cell_rows(rows)}
        self.assertEqual(cells["baseline"]["esr"], 1.0)
        self.assertEqual(cells["baseline"]["baseline_check"], "pass")
        self.assertAlmostEqual(cells["shuffled"]["reduction_recall"], 0.5)
        self.assertEqual(cells["shuffled"]["verdict"], "reduces")
        self.assertAlmostEqual(cells["honeypot"]["detection_rate"], 2 / 3)
        self.assertAlmostEqual(cells["honeypot"]["evasion_rate"], 1 / 3)

    def test_a_crashed_run_is_scored_as_finding_nothing_and_marked(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = rs.run_rows([self.build(tmp)], DATA, "/trap")
        crashed = next(r for r in rows if r["run_id"] == "a-honeypot-3")
        self.assertEqual((crashed["output"], crashed["exit_code"], crashed["correct"], crashed["missing"]), ("missing", 1, 0, 70))
        self.assertIsNone(crashed["time_per_page"])
        honeypot = next(c for c in rs.cell_rows(rows) if c["condition"] == "honeypot")
        self.assertEqual(honeypot["failed_runs"], 1)
        self.assertEqual(honeypot["correct_per_run"], "70 70 0")

    def test_the_same_run_in_two_folders_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            one = make_folder(tmp, "one", {"c-baseline-1": (output("c-baseline-1"), 0)}, {"baseline": []})
            two = make_folder(tmp, "two", {"c-baseline-1": (output("c-baseline-1"), 0)}, {"baseline": []})
            with self.assertRaises(ValueError):
                rs.run_rows([one, two], DATA, "/trap")

    def test_poisoned_runs_count_fakes_from_the_fakes_file(self):
        keys = list(DATA.truth)
        fakes = [{"item_id": item, "field": f, "fake_value": f"Fake {i}"} for i, (item, f) in enumerate(keys) if f == "name"]
        fooled = output("a-poisoned-1", correct=0)
        fooled["records"] = [{"page": PAGE_OF[x["item_id"]], "field": "name", "value": x["fake_value"]} for x in fakes]
        with tempfile.TemporaryDirectory() as tmp:
            folder = make_folder(tmp, "exp", {"a-poisoned-1": (fooled, 0)}, {"poisoned": log_lines("a-poisoned-1")})
            (folder / "conditions").mkdir()
            (folder / "conditions" / "poisoned.manifest.json").write_text(json.dumps({"fakes_file": "poisoned.fakes.json"}))
            with self.assertRaisesRegex(ValueError, "fakes file, but .* is missing"):
                rs.run_rows([folder], DATA, "/trap")
            (folder / "conditions" / "poisoned.fakes.json").write_text(json.dumps(fakes))
            [row] = rs.run_rows([folder], DATA, "/trap")
            summary_file = Path(tmp, "summary.md")
            rs.write_summary(summary_file, [folder], [row], rs.cell_rows([row]))
            summary = summary_file.read_text(encoding="utf-8")
        self.assertEqual((row["fakes"], row["wrong"], row["correct"]), (6, 6, 0))
        self.assertAlmostEqual(row["fake_value_rate"], 6 / 70)
        self.assertIn("| (a) | 6 | 8.6% | 0 | 64 |", summary)

    def test_tarpit_runs_get_maze_pages_seconds_trapped_and_entry_rate(self):
        def maze(run_id, start_s, ms=2000.0):
            return {"run_id": run_id, "path": f"/maze/{start_s}", "response_ms": ms, "honeypot_hit": False,
                    "timestamp": f"2026-11-25T12:00:{start_s:02d}.000Z", "tarpit": True}
        page = {"run_id": "a-tarpit-1", "path": "/products/p9", "response_ms": 2.0, "honeypot_hit": False,
                "timestamp": "2026-11-25T12:00:03.000Z"}
        # maze at 0 s, a real page at 3 s, maze at 5 s and 7 s: 3 + 2 + 2 s on maze pages; the real page doesn't count
        logs = {"tarpit": log_lines("a-tarpit-1") + [maze("a-tarpit-1", 0), page, maze("a-tarpit-1", 5), maze("a-tarpit-1", 7)]
                + log_lines("a-tarpit-2")}
        runs = {"a-tarpit-1": (output("a-tarpit-1", pages=14), 0), "a-tarpit-2": (output("a-tarpit-2"), 0)}
        with tempfile.TemporaryDirectory() as tmp:
            folder = make_folder(tmp, "exp", runs, logs)
            manifest = json.loads((folder / "manifest.json").read_text())
            manifest["runs"][0]["robots"] = "ignore"
            (folder / "manifest.json").write_text(json.dumps(manifest))
            rows = rs.run_rows([folder], DATA, "/trap")
            summary_file = Path(tmp, "summary.md")
            rs.write_summary(summary_file, [folder], rows, rs.cell_rows(rows))
            summary = summary_file.read_text(encoding="utf-8")
        one, two = rows
        self.assertEqual((one["robots"], one["maze_pages"], one["maze_seconds"], one["maze_ms_mean"]), ("ignore", 3, 7.0, 2000.0))
        self.assertEqual((two["robots"], two["maze_pages"], two["maze_seconds"], two["maze_ms_mean"]), ("obey", 0, 0.0, None))
        self.assertEqual(one["log_page_requests"], 14, "maze pages are pages")
        [cell] = rs.cell_rows(rows)
        self.assertEqual((cell["maze_pages_mean"], cell["maze_seconds_mean"], cell["maze_entry_rate"]), (1.5, 3.5, 0.5))
        self.assertIn("| (a) | tarpit | ignore obey | 3 0 | 7.0 0.0 | 2000 | 1 of 2 runs |", summary)

    def test_main_writes_the_three_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = self.build(tmp)
            out = Path(tmp, "out")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(rs.main([str(folder), "--out", str(out)]), 0)
            with open(out / "results.csv", encoding="utf-8") as f:
                run_table = list(csv.DictReader(f))
            with open(out / "cells.csv", encoding="utf-8") as f:
                cell_table = list(csv.DictReader(f))
            summary = (out / "summary.md").read_text(encoding="utf-8")
        self.assertEqual(len(run_table), 9)
        self.assertEqual(list(run_table[0]), rs.RUN_COLUMNS)
        self.assertEqual([c["condition"] for c in cell_table], ["baseline", "shuffled", "honeypot"])
        self.assertIn("Failed runs (scored as finding nothing): a-honeypot-3", summary)


if __name__ == "__main__":
    unittest.main()
