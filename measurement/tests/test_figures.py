"""Checks for measurement/figures.py: reading the CSVs, the tables, and (when matplotlib is installed) the figures.

Run with: python -m unittest discover -s measurement/tests -t .
"""

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

from measurement import figures as fg

CELL_COLUMNS = ["scraper", "condition", "runs", "failed_runs", "correct_per_run", "recall_mean", "recall_min", "recall_max",
                "precision_mean", "f1_mean", "esr", "reduction_recall", "reduction_f1", "verdict", "baseline_check",
                "fake_value_rate_mean", "time_per_page_mean", "time_per_page_min", "time_per_page_max", "honeypot_hits",
                "detection_rate", "evasion_rate"]


def cell(s, cond, correct, reduction, tpp, hits):
    r = correct / 70
    return {"scraper": s, "condition": cond, "runs": 3, "failed_runs": 0, "correct_per_run": f"{correct} {correct} {correct}",
            "recall_mean": r, "recall_min": r, "recall_max": r, "precision_mean": 1.0 if correct == 70 else 0.5,
            "f1_mean": r, "esr": 1.0 if correct == 70 else 0.0, "reduction_recall": reduction, "reduction_f1": reduction,
            "verdict": "baseline" if cond == "baseline" else ("stops" if r < 0.1 else "no effect"), "baseline_check": "pass",
            "fake_value_rate_mean": 0, "time_per_page_mean": tpp, "time_per_page_min": tpp, "time_per_page_max": tpp,
            "honeypot_hits": hits, "detection_rate": 1.0 if hits else 0.0, "evasion_rate": 0.0 if hits else 1.0}


ROWS = [cell("a", "baseline", 70, "", 0.01, 0), cell("a", "shuffled", 4, 1 - 4 / 70, 0.01, 0), cell("a", "honeypot", 70, 0, 0.01, 3),
        cell("d", "baseline", 70, "", 3.0, 0), cell("d", "shuffled", 70, 0, 3.0, 0), cell("d", "honeypot", 70, 0, 3.0, 0)]
COST = [{"condition": "baseline", "reading_order_mismatch_rate": 0, "fields": 70, "fields_out_of_order": 0},
        {"condition": "shuffled", "pixel_diff_max_percent": 0, "ssim_min": 1, "fields": 70, "fields_out_of_order": 70,
         "reading_order_mismatch_rate": 1, "html_change_percent": 21.2, "axe_violations": 0, "axe_new_vs_baseline": 0,
         "lh_score_change_mean": 0, "lh_fcp_ms_change_mean": -0.2, "lh_lcp_ms_change_mean": 0, "lh_tti_ms_change_mean": 22},
        {"condition": "honeypot", "pixel_diff_max_percent": 0, "ssim_min": 1, "fields": 70, "fields_out_of_order": 0,
         "reading_order_mismatch_rate": 0, "html_change_percent": 2.8, "axe_violations": 0, "axe_new_vs_baseline": 0,
         "lh_score_change_mean": 0, "lh_fcp_ms_change_mean": 0, "lh_lcp_ms_change_mean": 0, "lh_tti_ms_change_mean": -7}]


def write_inputs(tmp):
    cells = Path(tmp, "cells.csv")
    with open(cells, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CELL_COLUMNS)
        w.writeheader()
        w.writerows(ROWS)
    cost_dir = Path(tmp, "cost")
    cost_dir.mkdir()
    columns = sorted({k for r in COST for k in r}, key=lambda k: (k != "condition", k))
    with open(cost_dir / "cost.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(COST)
    return cells, cost_dir


class TablesTest(unittest.TestCase):
    def test_tables_hold_the_numbers_and_the_published_comparison(self):
        with tempfile.TemporaryDirectory() as tmp:
            cells_file, cost_dir = write_inputs(tmp)
            cells, cost = fg.read_cells(cells_file), fg.read_cost(cost_dir)
        self.assertIsNone(cells[("a", "baseline")]["reduction_recall"])
        text = fg.tables(cells, cost, ["a", "d"])
        self.assertIn("| (a) raw HTML | shuffled | 4 4 4 | 5.7% |", text)
        self.assertIn("94.3% | stops |", text)
        self.assertIn("| (d) adaptive | 0.00 | 1.00 | 0 |", text)
        self.assertIn("| shuffled | 0.000% | 1.0000 | 70/70 | +21.2% | 0 (0) | +0.0 | +0 ms | +0 ms | +22 ms | — |", text)
        self.assertIn("100% (88.7% → 0%) | WebCloak", text)
        self.assertIn("300×", text)


@unittest.skipUnless(importlib.util.find_spec("matplotlib"), "matplotlib not installed (pip install -r requirements.txt)")
class FiguresTest(unittest.TestCase):
    def test_every_figure_is_written(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fg.style(plt)
        with tempfile.TemporaryDirectory() as tmp:
            cells_file, cost_dir = write_inputs(tmp)
            cells, cost = fg.read_cells(cells_file), fg.read_cost(cost_dir)
            for name, draw in (("fig1.png", lambda p: fg.fig_recall(plt, cells, ["a", "d"], p)),
                               ("fig2.png", lambda p: fg.fig_reduction(plt, cells, ["a", "d"], p)),
                               ("fig3.png", lambda p: fg.fig_protection_vs_cost(plt, cells, cost, ["a", "d"], p)),
                               ("fig4.png", lambda p: fg.fig_honeypot(plt, cells, ["a", "d"], p)),
                               ("fig6.png", lambda p: fg.fig_published(plt, cells, cost, ["a", "d"], p)),
                               ("fig5.png", lambda p: fg.fig_fields(plt, [("Product", "Price", 18, 18), ("Article", "Tags", 0, 6)], p))):
                path = Path(tmp, name)
                draw(path)
                self.assertGreater(path.stat().st_size, 5000, name)


if __name__ == "__main__":
    unittest.main()
