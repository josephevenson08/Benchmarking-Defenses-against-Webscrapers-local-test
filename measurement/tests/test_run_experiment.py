"""Checks for measurement/run_experiment.py that need no server or real scraper.

Run with: python -m unittest discover -s measurement/tests -t .
"""

import tempfile
import unittest
from pathlib import Path

from measurement import run_experiment as rx
from scoring.score import parse_run_id

WRITES_OUTPUT = """import argparse, json
p = argparse.ArgumentParser()
p.add_argument("--start-url"); p.add_argument("--run-id"); p.add_argument("--out"); p.add_argument("--robots")
a = p.parse_args()
print("crawling", a.start_url, a.run_id, "robots", a.robots)
json.dump({"run": {"run_id": a.run_id}, "pages": [], "records": []}, open(a.out, "w"))
"""
SLEEPS = "import time\nprint('started', flush=True)\ntime.sleep(30)\n"


class PlanTest(unittest.TestCase):
    def test_finds_scrapers_by_letter(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("a_raw_html.py", "b_browser_text.py", "notes.py", "z_other.py", "c_llm_text.py"):
                Path(tmp, name).write_text("", encoding="utf-8")
            found = rx.find_scrapers(tmp)
        self.assertEqual(sorted(found), ["a", "b", "c"])
        self.assertEqual(found["c"].name, "c_llm_text.py")

    def test_run_ids_are_the_form_the_scoring_script_reads(self):
        self.assertEqual(rx.run_id("a", "shuffled", 2), "a-shuffled-2")
        self.assertEqual(parse_run_id(rx.run_id("d", "honeypot", 3)), ("d", "honeypot", 3))

    def test_plan_covers_every_cell_in_order(self):
        runs = rx.plan(["a", "b"], ["baseline", "shuffled", "honeypot"], 3)
        self.assertEqual(len(runs), 18)
        self.assertEqual([r["run_id"] for r in runs[:4]], ["a-baseline-1", "a-baseline-2", "a-baseline-3", "b-baseline-1"])
        self.assertEqual(runs[-1]["run_id"], "b-honeypot-3")
        self.assertEqual(len({r["run_id"] for r in runs}), 18)


class RunScraperTest(unittest.TestCase):
    def test_saves_output_and_what_it_printed(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp, "a_fake.py")
            script.write_text(WRITES_OUTPUT, encoding="utf-8")
            out, log = Path(tmp, "a-baseline-1.json"), Path(tmp, "a-baseline-1.log")
            code, wall = rx.run_scraper(script, "a-baseline-1", 3100, out, log, timeout=30)
            self.assertEqual(code, 0)
            self.assertTrue(out.exists())
            self.assertIn("crawling http://127.0.0.1:3100/ a-baseline-1 robots obey", log.read_text(encoding="utf-8"))
            self.assertGreaterEqual(wall, 0)

    def test_passes_the_robots_setting(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp, "a_fake.py")
            script.write_text(WRITES_OUTPUT, encoding="utf-8")
            log = Path(tmp, "a-tarpit-1.log")
            code, _ = rx.run_scraper(script, "a-tarpit-1", 3100, Path(tmp, "a-tarpit-1.json"), log, timeout=30, robots="ignore")
            self.assertEqual(code, 0)
            self.assertIn("robots ignore", log.read_text(encoding="utf-8"))

    def test_a_run_that_takes_too_long_is_stopped_and_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp, "a_slow.py")
            script.write_text(SLEEPS, encoding="utf-8")
            log = Path(tmp, "slow.log")
            code, wall = rx.run_scraper(script, "a-baseline-1", 3100, Path(tmp, "out.json"), log, timeout=1)
            self.assertIsNone(code)
            self.assertIn("stopped after 1 s", log.read_text(encoding="utf-8"))
            self.assertLess(wall, 10)

    def test_summary_lists_failed_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = {"started_at": "s", "finished_at": "f", "commit": "abc", "scrapers": {"a": "a_raw_html.py"},
                        "conditions": ["baseline"], "runs_per_cell": 2, "runs": [
                            {"run_id": "a-baseline-1", "exit_code": 0, "wall_s": 0.2,
                             "quick_score": {"correct": 70, "scored_fields": 70, "accuracy": 1.0, "pages_fetched": 10, "time_per_page": 0.02}},
                            {"run_id": "a-baseline-2", "exit_code": None, "wall_s": 1800}]}
            rx.write_summary(Path(tmp), manifest)
            text = Path(tmp, "summary.md").read_text(encoding="utf-8")
        self.assertIn("70/70 = 1.000", text)
        self.assertIn("timeout", text)
        self.assertIn("1 of 2 runs finished", text)
        self.assertIn("Failed: a-baseline-2", text)


if __name__ == "__main__":
    unittest.main()
