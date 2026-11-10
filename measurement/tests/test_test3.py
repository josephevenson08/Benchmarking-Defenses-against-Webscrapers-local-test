"""Checks for the record comparison in measurement/test3.py (no server or scraper needed).

Run with: python -m unittest discover -s measurement/tests -t .
"""

import unittest

from measurement.test3 import compare_records


class CompareRecordsTest(unittest.TestCase):
    def test_identical_records_have_no_differences(self):
        recs = [{"field": "name", "value": "Lamp"}, {"field": "price", "value": "$34.50"}]
        diff = compare_records(recs, list(reversed(recs)))
        self.assertEqual(diff, {"missing": [], "extra": [], "wrong": [], "duplicates": False})

    def test_reports_missing_extra_and_wrong_fields(self):
        expected = [{"field": "name", "value": "Lamp"}, {"field": "price", "value": "$34.50"}]
        got = [{"field": "price", "value": "$35.00"}, {"field": "sku", "value": "X-1"}]
        diff = compare_records(expected, got)
        self.assertEqual(diff["missing"], ["name"])
        self.assertEqual(diff["extra"], ["sku"])
        self.assertEqual(diff["wrong"], [{"field": "price", "expected": "$34.50", "got": "$35.00"}])

    def test_flags_a_field_written_twice(self):
        got = [{"field": "name", "value": "Lamp"}, {"field": "name", "value": "Lamp"}]
        self.assertTrue(compare_records([{"field": "name", "value": "Lamp"}], got)["duplicates"])


if __name__ == "__main__":
    unittest.main()
