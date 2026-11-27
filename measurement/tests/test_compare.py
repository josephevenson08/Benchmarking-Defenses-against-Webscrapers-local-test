"""Checks for measurement/compare.py: the three-measure comparison of scrapers and defenses (D118).

Run with: python -m unittest discover -s measurement/tests -t .
"""
import importlib.util
import tempfile
import unittest
from pathlib import Path


def cell(recall, verdict, detection=0.0):
    return {"recall_mean": recall, "verdict": verdict, "detection_rate": detection, "runs": 3.0}


CELLS = {("a", "baseline"): cell(1.0, "baseline"), ("a", "shuffled"): cell(4 / 70, "stops"),
         ("a", "honeypot"): cell(1.0, "no effect", 1.0), ("a", "poisoned"): cell(0.0, "stops"),
         ("d", "baseline"): cell(1.0, "baseline"), ("d", "shuffled"): cell(1.0, "no effect"),
         ("d", "honeypot"): cell(1.0, "no effect", 0.0), ("d", "poisoned"): cell(1.0, "no effect")}
COST = {"shuffled": {"lh_lcp_ms_change_mean": 0.2, "fields_out_of_order": 70.0, "fields": 70.0, "fakes_visible_max_s": None},
        "poisoned": {"lh_lcp_ms_change_mean": 2.0, "fields_out_of_order": 0.0, "fields": 70.0, "fakes_visible_max_s": 2.03}}


@unittest.skipUnless(importlib.util.find_spec("matplotlib"), "matplotlib not installed (pip install -r requirements.txt)")
class CompareTest(unittest.TestCase):
    def test_percentages_keep_a_decimal_only_when_needed(self):
        from measurement import compare as cp
        self.assertEqual([cp.pct(1.0), cp.pct(4 / 70), cp.pct(0.695238), cp.pct(0.0)], ["100%", "5.7%", "69.5%", "0%"])

    def test_tables_have_the_three_measures_and_what_they_show(self):
        from measurement import compare as cp
        text = cp.tables(CELLS, COST)
        self.assertIn("| (a) raw HTML | 100% | 5.7% (stops) | 100% (no effect) | 0% (stops) |", text)
        self.assertIn("- **Shuffling** stops (a); has no effect on (d).", text)
        self.assertIn("| (d) adaptive | 0% (0 of 3 runs) |", text)
        self.assertIn("- **Honeypot** catches (a) in every run; never catches (d).", text)
        self.assertIn("| Shuffling | +0 ms | 70 of 70 | none |", text)
        self.assertIn("| Poisoning | +2 ms | 0 of 70 | 2.03 s |", text)

    def test_false_positives_are_listed_when_given(self):
        from measurement import compare as cp
        fp = {"conditions": [{"condition": "honeypot", "caught": 0, "sessions": 20, "false_positive_rate": 0.0},
                             {"condition": "tarpit", "caught": 15, "sessions": 20, "false_positive_rate": 0.75}]}
        text = cp.tables(CELLS, COST, fp)
        self.assertIn("| honeypot | 0 of 20 | 0% |", text)
        self.assertIn("| tarpit | 15 of 20 | 75% |", text)
        self.assertNotIn("False positives", cp.tables(CELLS, COST))

    def test_both_charts_are_written(self):
        from measurement import compare as cp
        with tempfile.TemporaryDirectory() as tmp:
            for name, draw in (("1.png", cp.accuracy_grid), ("2.png", cp.detection_chart)):
                draw(CELLS, Path(tmp, name))
                self.assertGreater(Path(tmp, name).stat().st_size, 5000, name)


if __name__ == "__main__":
    unittest.main()
