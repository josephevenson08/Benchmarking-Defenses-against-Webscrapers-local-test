"""Checks for measurement/cross_check.py's own rules (the independent recount must itself be right).

Run with: python -m unittest discover -s measurement/tests -t .
"""

import unittest

from measurement import cross_check as xc


class MatchingRulesTest(unittest.TestCase):
    """The examples in docs/scraper-output.md's matching-rules table."""

    def same(self, field, a, b):
        return xc.comparable(field, a) == xc.comparable(field, b)

    def test_examples_from_the_rules_table(self):
        self.assertTrue(self.same("price", "$89.99", 89.99))
        self.assertTrue(self.same("price", "89.99", "$89.99"))
        self.assertTrue(self.same("rating", "4.50", "4.5"))
        self.assertTrue(self.same("review_count", "1,284", "1284"))
        self.assertTrue(self.same("release_date", " 2024-09-12 ", "2024-09-12"))
        self.assertTrue(self.same("tags", "kitchen, Cookware,cleaning", "cookware, cleaning, kitchen"))
        self.assertTrue(self.same("name", "larkfield studio  headphones", "Larkfield Studio Headphones"))

    def test_malformed_and_missing(self):
        self.assertEqual(xc.comparable("price", "$8a.99")[0], "malformed")
        self.assertEqual(xc.comparable("review_count", "12.5")[0], "malformed")
        self.assertTrue(xc.blank(None) and xc.blank("  ") and not xc.blank("0"))


class RecountTest(unittest.TestCase):
    def test_hand_counted_test2_fixture(self):
        checks = xc.Checks()
        xc.check_fixture(checks)
        [(name, ok, detail)] = checks.items
        self.assertTrue(ok, detail)

    def test_conflicting_duplicates_are_wrong_and_identical_ones_count_once(self):
        truth = {("p1", "price"): "$89.99", ("p1", "sku"): "LF-HP-2041"}
        pages = {"/products/p1": "p1"}
        out = {"records": [{"page": "/products/p1", "field": "price", "value": "$89.99"},
                           {"page": "/products/p1/", "field": "price", "value": "89.99"},
                           {"page": "/products/p1", "field": "sku", "value": "LF-HP-2041"},
                           {"page": "/products/p1", "field": "sku", "value": "LF-HP-2047"}]}
        t = xc.recount(out, truth, pages)
        self.assertEqual((t["correct"], t["wrong"], t["conflict"], t["missing"]), (1, 1, 1, 0))


class ReadingOrderTest(unittest.TestCase):
    BASE = '<div class="fields"><div class="field"><span class="label">Name</span><span class="value">Lamp</span></div>' \
           '<div class="field"><span class="label">Price</span><span class="value">$5</span></div></div></main>'
    SHUFFLED = '<div class="fields"><span class="value" style="order: 3">$5</span><span class="label" style="order: 0">Name</span>' \
               '<span class="label" style="order: 2">Price</span><span class="value" style="order: 1">Lamp</span></div></main>'

    def test_fields_and_order_from_html(self):
        base, shuffled = xc.html_fields(self.BASE), xc.html_fields(self.SHUFFLED)
        self.assertEqual(base[0], ("label", "Name", 0))
        self.assertEqual(xc.out_of_order(base, base), (2, 0))
        self.assertEqual(xc.out_of_order(base, shuffled), (2, 2))


if __name__ == "__main__":
    unittest.main()
