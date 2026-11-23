"""Checks for measurement/test5.py's own rules (what counts as a leak, and as a field showing its value).

Run with: python -m unittest discover -s measurement/tests -t .
"""

import json
import tempfile
import unittest
from pathlib import Path

from measurement import test5
from scoring.score import DataList

DATA = DataList.load()


class LeakTest(unittest.TestCase):
    def test_a_match_must_stand_alone(self):
        self.assertEqual(test5.standalone("4.5", "<span>$64.50</span>"), [])
        self.assertEqual(test5.standalone("Lark", "Larkfield"), [])
        self.assertEqual(len(test5.standalone("4.5", "<span>4.5</span>")), 1)
        self.assertEqual(len(test5.standalone("$89.99", "price $89.99.")), 1)

    def test_escaped_values_are_found(self):
        self.assertEqual(len(test5.standalone("A & B", "<span>A &amp; B</span>")), 1)

    def test_leaks_name_the_page_and_field(self):
        truth = {("p1", "brand"): "Larkfield", ("p1", "rating"): "4.5"}
        found = test5.leaks({"/products/p1": "<span>Larkfield Pro</span><span>$64.50</span>"}, truth)
        self.assertEqual([(f["page"], f["item_id"], f["field"]) for f in found], [("/products/p1", "p1", "brand")])

    def test_an_item_page_is_searched_for_its_own_values_only(self):
        truth = {("p1", "availability"): "In stock", ("p2", "availability"): "Low stock"}
        pages = {"/products/p1": "<span>Low stock</span>", "/products/p2": "<span>In stock</span>", "/": "<p>Low stock</p>"}
        found = test5.leaks(pages, truth, {"/products/p1": "p1", "/products/p2": "p2"})
        self.assertEqual([(f["page"], f["item_id"]) for f in found], [("/", "p2")])


class CompareTest(unittest.TestCase):
    def test_fields_are_matched_by_label_and_compared_as_trimmed_text(self):
        shown = [{"label": "Price ", "value": " $74.99"}, {"label": "Name", "value": "Lamp"}]
        expected = [("price", "Price", "$74.99"), ("name", "Name", "Desk Lamp"), ("sku", "SKU", "X-1")]
        wrong = test5.compare(shown, expected)
        self.assertEqual([(w["field"], w["shown"]) for w in wrong], [("name", "Lamp"), ("sku", None)])


class FakesFileTest(unittest.TestCase):
    def test_each_bad_fake_is_listed_and_the_rest_are_kept(self):
        rows = [{"item_id": i, "field": f, "fake_value": "Other " + v} for (i, f), v in DATA.truth.items()]
        rows[3]["fake_value"] = "$8a.99"  # p1 price: malformed
        rows[0]["fake_value"] = DATA.truth[("p1", "name")].lower()  # p1 name: the real value
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "poisoned.fakes.json")
            path.write_text(json.dumps(rows[:-1]), encoding="utf-8")
            fakes, problems = test5.check_fakes_file(path, DATA)
            missing, none = test5.check_fakes_file(Path(tmp, "nope.json"), DATA)
        self.assertEqual(len(fakes), 69)
        self.assertTrue(any("('p1', 'name')" in p and "equals the real value" in p for p in problems), problems)
        self.assertTrue(any("('p1', 'price')" in p for p in problems), problems)
        self.assertIn("no fake for a2 summary", problems)
        self.assertEqual(missing, {})
        self.assertIn("export fakeValue", none[0])


if __name__ == "__main__":
    unittest.main()
