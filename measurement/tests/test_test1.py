"""Checks for the page and field counting in measurement/test1.py (no server or scraper needed).

Run with: python -m unittest discover -s measurement/tests -t .
"""

import json
import tempfile
import unittest
from pathlib import Path

from measurement.test1 import condition_counts, counts_ok

ROW = '<div class="field"><span class="label">L{n}</span><span class="value">V{n}</span></div>'


def make_condition(tmp, name, item_pages, fields_per_page, extra_pages=2):
    site = Path(tmp, name)
    pages = []
    for i in range(extra_pages):
        (site / f"other{i}.html").parent.mkdir(parents=True, exist_ok=True)
        (site / f"other{i}.html").write_text("<p>no fields</p>", encoding="utf-8")
        pages.append({"path": f"/other{i}", "file": f"other{i}.html", "type": "home"})
    for i in range(item_pages):
        rows = "".join(ROW.format(n=k) for k in range(fields_per_page))
        (site / f"item{i}.html").write_text(f'<div class="fields">{rows}</div>', encoding="utf-8")
        pages.append({"path": f"/item{i}", "file": f"item{i}.html", "type": "product"})
    manifest = {"condition": name, "scored_fields": item_pages * fields_per_page, "pages": pages}
    Path(tmp, f"{name}.manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


class ConditionCountsTest(unittest.TestCase):
    def test_counts_pages_and_label_value_pairs(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_condition(tmp, "baseline", item_pages=7, fields_per_page=10, extra_pages=3)
            c = condition_counts(tmp, "baseline")
        self.assertEqual((c["html_files"], c["manifest_pages"]), (10, 10))
        self.assertEqual((c["manifest_scored_fields"], c["label_elements"], c["value_elements"]), (70, 70, 70))
        self.assertTrue(counts_ok(c))

    def test_a_missing_page_or_field_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_condition(tmp, "short", item_pages=7, fields_per_page=10, extra_pages=2)
            self.assertFalse(counts_ok(condition_counts(tmp, "short")))
            make_condition(tmp, "thin", item_pages=8, fields_per_page=8, extra_pages=2)
            self.assertFalse(counts_ok(condition_counts(tmp, "thin")))


if __name__ == "__main__":
    unittest.main()
