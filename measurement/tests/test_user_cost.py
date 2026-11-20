"""Checks for measurement/user_cost.py that need no browser.

Run with: python -m unittest discover -s measurement/tests -t .
"""

import json
import tempfile
import unittest
from pathlib import Path

from measurement import user_cost as uc


def el(kind, text, top, left=0):
    return {"kind": kind, "text": text, "top": top, "left": left}


# Baseline: each label is followed by its value, in rows, in the source and on screen.
BASELINE = [el("label", "Name", 0), el("value", "Lamp", 0, 200), el("label", "Price", 40), el("value", "$34.50", 40, 200)]
# Shuffled: the source order is mixed; CSS puts every element back where the baseline shows it.
SHUFFLED = [el("value", "$34.50", 40, 200), el("label", "Name", 0), el("label", "Price", 40), el("value", "Lamp", 0, 200)]


class ScreenOrderTest(unittest.TestCase):
    def test_top_to_bottom_then_left_to_right(self):
        order = uc.screen_order(SHUFFLED)
        self.assertEqual([e["text"] for e in order], ["Name", "Lamp", "Price", "$34.50"])

    def test_subpixel_differences_count_as_one_row(self):
        order = uc.screen_order([el("value", "v", 10.2, 200), el("label", "l", 9.9, 0)])
        self.assertEqual([e["kind"] for e in order], ["label", "value"])

    def test_pairs_come_from_the_baseline(self):
        self.assertEqual(uc.pairs_of(BASELINE), [("Name", "Lamp"), ("Price", "$34.50")])


class ReadingOrderTest(unittest.TestCase):
    def test_baseline_is_in_order(self):
        self.assertEqual(uc.reading_order(BASELINE, uc.pairs_of(BASELINE)), (2, 0))

    def test_shuffled_fields_are_out_of_order(self):
        self.assertEqual(uc.reading_order(SHUFFLED, uc.pairs_of(BASELINE)), (2, 2))

    def test_a_field_counts_only_if_its_label_or_value_moved(self):
        # Name and Lamp keep positions 0 and 1; Price and $34.50 swap in the source.
        source = [el("label", "Name", 0), el("value", "Lamp", 0, 200), el("value", "$34.50", 40, 200), el("label", "Price", 40)]
        self.assertEqual(uc.reading_order(source, uc.pairs_of(BASELINE)), (2, 1))

    def test_a_missing_value_counts_as_out_of_order(self):
        self.assertEqual(uc.reading_order(BASELINE[:3], uc.pairs_of(BASELINE)), (2, 1))

    def test_pages_without_fields(self):
        self.assertEqual(uc.reading_order([], []), (0, 0))


class SizesAndRowsTest(unittest.TestCase):
    def test_html_sizes_from_the_generated_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            pages = [{"path": "/", "file": "index.html"}, {"path": "/products/p1", "file": "products/p1.html"}]
            Path(tmp, "shuffled.manifest.json").write_text(json.dumps({"pages": pages}), encoding="utf-8")
            Path(tmp, "shuffled", "products").mkdir(parents=True)
            Path(tmp, "shuffled", "index.html").write_bytes(b"x" * 120)
            Path(tmp, "shuffled", "products", "p1.html").write_bytes(b"x" * 300)
            self.assertEqual(uc.html_sizes("shuffled", tmp), {"/": 120, "/products/p1": 300})

    def test_rows_and_condition_totals(self):
        sizes = {"/": 120, "/products/p1": 300}
        base_sizes = {"/": 100, "/products/p1": 250}
        pixels = {"pages": [{"page": "index.png", "percent": 0.0, "ssim": 1.0},
                            {"page": "products-p1.png", "percent": 0.5, "ssim": 0.98}],
                  "mean_percent": 0.25, "max_percent": 0.5, "mean_ssim": 0.99, "min_ssim": 0.98}
        rows = uc.page_rows("shuffled", sizes, base_sizes, {"/": [], "/products/p1": SHUFFLED},
                            {"/": [], "/products/p1": BASELINE}, pixels)
        p1 = next(r for r in rows if r["page"] == "/products/p1")
        self.assertEqual((p1["fields"], p1["fields_out_of_order"], p1["ssim"]), (2, 2, 0.98))
        self.assertAlmostEqual(p1["html_change_percent"], 20.0)
        row = uc.condition_row("shuffled", rows, pixels, sum(base_sizes.values()))
        self.assertEqual((row["fields"], row["fields_out_of_order"], row["reading_order_mismatch_rate"]), (2, 2, 1.0))
        self.assertAlmostEqual(row["html_change_percent"], 20.0)
        self.assertAlmostEqual(row["html_change_max_page_percent"], 20.0)
        self.assertEqual((row["ssim_mean"], row["pixel_diff_max_percent"]), (0.99, 0.5))


class AxeAndLighthouseTest(unittest.TestCase):
    def test_wcag_level_from_axe_tags(self):
        self.assertEqual(uc.wcag_level(["cat.color", "wcag2aa", "wcag143"]), "AA")
        self.assertEqual(uc.wcag_level(["wcag2a", "wcag412"]), "A")
        self.assertEqual(uc.wcag_level(["wcag21aa", "wcag2aaa"]), "AA")
        self.assertEqual(uc.wcag_level(["cat.semantics", "best-practice"]), "best-practice")

    def test_axe_counts_and_new_violations_against_baseline(self):
        base_axe = {"/products/p1": [{"id": "region", "impact": "moderate", "tags": ["best-practice"], "nodes": 2}]}
        axe = {"/products/p1": [{"id": "region", "impact": "moderate", "tags": ["best-practice"], "nodes": 3},
                                {"id": "link-name", "impact": "serious", "tags": ["wcag2a", "wcag412"], "nodes": 1}]}
        rows = uc.page_rows("honeypot", {"/products/p1": 300}, {"/products/p1": 250}, {"/products/p1": BASELINE},
                            {"/products/p1": BASELINE}, None, axe=axe, base_axe=base_axe)
        [row] = rows
        self.assertEqual((row["axe_violations"], row["axe_new_vs_baseline"]), (4, 2))
        self.assertEqual(row["axe_rules"], "link-name:1 region:3")
        totals = uc.condition_row("honeypot", rows, None, 250)
        self.assertEqual((totals["axe_serious"], totals["axe_moderate"], totals["axe_critical"]), (1, 3, 0))
        self.assertEqual((totals["axe_level_A"], totals["axe_level_best-practice"]), (1, 3))

    def test_lighthouse_medians_and_changes_from_baseline(self):
        def report(score, fcp):
            return {"pages": [{"path": "/", "median": {"score": score, "fcp_ms": fcp, "lcp_ms": fcp, "tti_ms": fcp + 10}},
                              {"path": "/products/p1", "median": {"score": score - 2, "fcp_ms": fcp, "lcp_ms": fcp, "tti_ms": fcp}}]}
        sizes = {"/": 100, "/products/p1": 200}
        rows = uc.page_rows("shuffled", sizes, sizes, {}, {}, None, lh=report(97, 650), base_lh=report(100, 600))
        p1 = next(r for r in rows if r["page"] == "/products/p1")
        self.assertEqual((p1["lh_score"], p1["lh_score_change"], p1["lh_fcp_ms_change"]), (95, -3, 50))
        totals = uc.condition_row("shuffled", rows, None, 300)
        self.assertEqual((totals["lh_score_mean"], totals["lh_score_change_mean"]), (96, -3))
        self.assertEqual(totals["lh_tti_ms_change_mean"], 50)

    def test_without_axe_or_lighthouse_the_columns_stay_empty(self):
        rows = uc.page_rows("shuffled", {"/": 100}, {"/": 100}, {}, {}, None)
        self.assertNotIn("axe_violations", rows[0])
        self.assertNotIn("lh_score_mean", uc.condition_row("shuffled", rows, None, 100))


if __name__ == "__main__":
    unittest.main()
