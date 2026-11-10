"""Checks for the parts of measurement/test4.py that need no browser.

Run with: python -m unittest discover -s measurement/tests -t .
"""

import tempfile
import unittest
from pathlib import Path

from measurement.test4 import compare_folders, field_sequence, pairs_kept

BASELINE = """<main><h1>Product details</h1>
    <div class="fields">
      <div class="field"><span class="label">Name</span><span class="value">Lamp &amp; Co</span></div>
      <div class="field"><span class="label">Price</span><span class="value">$34.50</span></div>
    </div>
  </main>"""

SHUFFLED = """<main><h1>Product details</h1>
    <div class="fields">
      <span class="value" style="order: 3">$34.50</span>
      <span class="label" style="order: 0">Name</span>
      <span class="label" style="order: 2">Price</span>
      <span class="value" style="order: 1">Lamp &amp; Co</span>
    </div>
  </main>"""


class FieldSequenceTest(unittest.TestCase):
    def test_reads_rows_and_loose_spans_in_source_order(self):
        self.assertEqual(field_sequence(BASELINE), [
            ("label", "Name"), ("value", "Lamp & Co"), ("label", "Price"), ("value", "$34.50")])
        self.assertEqual(field_sequence(SHUFFLED), [
            ("value", "$34.50"), ("label", "Name"), ("label", "Price"), ("value", "Lamp & Co")])

    def test_ignores_spans_outside_the_fields_block(self):
        html = '<span class="label">Outside</span>' + BASELINE
        self.assertEqual(len(field_sequence(html)), 4)


class PairsKeptTest(unittest.TestCase):
    def test_counts_labels_still_followed_by_their_own_value(self):
        base = field_sequence(BASELINE)
        self.assertEqual(pairs_kept(base, base), 2)
        self.assertEqual(pairs_kept(base, field_sequence(SHUFFLED)), 0)
        partly = [("label", "Name"), ("value", "Lamp & Co"), ("value", "$34.50"), ("label", "Price")]
        self.assertEqual(pairs_kept(base, partly), 1)


class CompareFoldersTest(unittest.TestCase):
    def test_reports_differing_and_missing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp, "a"), Path(tmp, "b")
            for folder in (a, b):
                (folder / "products").mkdir(parents=True)
                (folder / "index.html").write_text("same", encoding="utf-8")
            (a / "products" / "p1.html").write_text("one", encoding="utf-8")
            (b / "products" / "p1.html").write_text("two", encoding="utf-8")
            (a / "only-a.txt").write_text("x", encoding="utf-8")
            result = compare_folders(a, b)
        self.assertEqual(result["files"], 3)
        self.assertEqual(result["differing"], ["products/p1.html"])
        self.assertEqual(result["only_in_first"], ["only-a.txt"])
        self.assertEqual(result["only_in_second"], [])


if __name__ == "__main__":
    unittest.main()
