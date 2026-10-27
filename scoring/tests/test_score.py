"""Tests for the scoring script. Run from the repository root:

    python -m unittest discover -s scoring/tests -t .
"""
import csv
import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from scoring.score import (
    CONFLICT, CORRECT, FAKE, MALFORMED, MISSING, WRONG,
    DataList, Malformed, load_fakes, load_output, main, normalize, normalize_page,
    parse_run_id, score_file, score_run,
)

ROOT = Path(__file__).resolve().parents[2]
TEST2 = ROOT / "scoring" / "fixtures" / "test2"
DATA = DataList.load()


def all_correct_records():
    """A perfect scraper output: one record per scored field, with the real value."""
    page = {item_id: path for path, item_id in DATA.pages.items()}
    return [{"page": page[item_id], "field": f, "value": v} for (item_id, f), v in DATA.truth.items()]


def run(records, pages=10, seconds=1.0, run_id="a-baseline-1"):
    return {
        "run": {"run_id": run_id, "scraper": run_id[0], "seconds": seconds},
        "pages": [{"path": f"/page{i}", "status": 200, "error": None} for i in range(pages)],
        "records": records,
    }


def status(score, item_id, field):
    return next(r.status for r in score.results if (r.item_id, r.field) == (item_id, field))


class Test2HandCalculated(unittest.TestCase):
    """§5 Test 2: Joseph's hand-made fixture and his hand calculation in expected.md."""

    def setUp(self):
        self.score = score_file(TEST2 / "output.json", TEST2 / "fakes.json")

    def test_matches_the_numbers_in_expected_md(self):
        text = (TEST2 / "expected.md").read_text(encoding="utf-8")

        def last_number(label):
            line = next(l for l in text.splitlines() if label in l)
            return float(re.findall(r"\d+(?:\.\d+)?", line)[-1])

        self.assertAlmostEqual(self.score.accuracy, last_number("Accuracy"), places=3)
        self.assertAlmostEqual(self.score.fake_value_rate, last_number("Fake-value rate"), places=3)

    def test_counts(self):
        s = self.score
        self.assertEqual(
            (s.scored_fields, s.correct, s.wrong, s.fakes, s.malformed, s.count(WRONG), s.missing),
            (70, 63, 4, 2, 1, 1, 3),
        )
        self.assertEqual(s.accuracy, 63 / 70)
        self.assertEqual(s.fake_value_rate, 2 / 70)

    def test_each_special_field(self):
        expected = {
            ("p1", "category"): MISSING,       # no record
            ("p1", "price"): MALFORMED,        # $89O.99
            ("p1", "review_count"): WRONG,     # 1,289
            ("p2", "sku"): MISSING,            # ""
            ("p3", "price"): FAKE,             # $41.00
            ("a1", "publish_date"): FAKE,      # 2025-05-19
            ("a2", "publish_date"): MISSING,   # null
        }
        for (item_id, field), want in expected.items():
            self.assertEqual(status(self.score, item_id, field), want, f"{item_id}.{field}")
        others = [r for r in self.score.results if (r.item_id, r.field) not in expected]
        self.assertEqual(len(others), 63)
        self.assertTrue(all(r.status == CORRECT for r in others))

    def test_run_details(self):
        s = self.score
        self.assertEqual((s.run_id, s.scraper, s.condition, s.run_number), ("a-poisoned-1", "a", "poisoned", 1))
        self.assertEqual((s.pages_fetched, s.time_per_page, s.ignored_records), (10, 0.1, 0))


class MatchingRules(unittest.TestCase):
    """The approved rules in docs/scraper-output.md (D33)."""

    def assertSame(self, field, a, b):
        self.assertEqual(normalize(field, a), normalize(field, b), f"{field}: {a!r} vs {b!r}")

    def test_price(self):
        for value in ("$89.99", "89.99", 89.99, "$ 89.99", "89.990"):
            self.assertSame("price", value, "$89.99")
        self.assertSame("price", "$1,089.50", "1089.5")
        for value in ("$8a.99", "$89O.99", "eighty", "", "-89.99", "89.99 USD"):
            with self.assertRaises(Malformed, msg=value):
                normalize("price", value)

    def test_rating_and_review_count(self):
        self.assertSame("rating", "4.50", "4.5")
        self.assertSame("rating", 4.5, "4.5")
        self.assertSame("review_count", "1,284", "1284")
        self.assertSame("review_count", 1284, "1,284")
        for field, value in (("rating", "4,5"), ("rating", "four"), ("review_count", "1284.5"), ("review_count", "12a")):
            with self.assertRaises(Malformed, msg=f"{field}={value}"):
                normalize(field, value)

    def test_dates_are_exact_text(self):
        self.assertSame("release_date", " 2024-09-12 ", "2024-09-12")
        self.assertNotEqual(normalize("release_date", "2024-9-12"), normalize("release_date", "2024-09-12"))

    def test_tags_are_a_set_ignoring_order_and_case(self):
        self.assertSame("tags", "kitchen, Cookware,cleaning", "cookware, cleaning, kitchen")
        self.assertNotEqual(normalize("tags", "cookware, kitchen"), normalize("tags", "cookware, cleaning, kitchen"))

    def test_other_text_ignores_case_and_extra_spaces(self):
        self.assertSame("name", "larkfield   studio headphones ", "Larkfield Studio Headphones")
        self.assertNotEqual(normalize("name", "Larkfield Studio"), normalize("name", "Larkfield Studio Headphones"))


class EdgeCases(unittest.TestCase):
    """The cases named in the midterm's prompt: missing fields, malformed values, empty outputs, duplicates."""

    def test_perfect_run_scores_one(self):
        s = score_run(run(all_correct_records()), DATA)
        self.assertEqual((s.correct, s.accuracy, s.fake_value_rate, s.missing), (70, 1.0, 0.0, 0))

    def test_three_forms_of_missing(self):
        records = all_correct_records()
        records = [r for r in records if (r["page"], r["field"]) != ("/products/p1", "name")]
        for r in records:
            if (r["page"], r["field"]) == ("/products/p2", "name"):
                r["value"] = None
            if (r["page"], r["field"]) == ("/products/p3", "name"):
                r["value"] = "   "
        s = score_run(run(records), DATA)
        self.assertEqual(s.missing, 3)
        self.assertEqual({status(s, p, "name") for p in ("p1", "p2", "p3")}, {MISSING})

    def test_empty_outputs_score_zero_without_crashing(self):
        for output in ({}, {"records": []}, run([])):
            s = score_run(output, DATA)
            self.assertEqual((s.correct, s.missing, s.accuracy), (0, 70, 0.0))
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty.json"
            empty.write_text("", encoding="utf-8")
            self.assertEqual(load_output(empty), {})
            self.assertEqual(score_file(empty).missing, 70)

    def test_identical_duplicates_count_once(self):
        records = all_correct_records()
        records.append({"page": "/products/p1", "field": "price", "value": "89.99"})  # same value, other format
        s = score_run(run(records), DATA)
        self.assertEqual((status(s, "p1", "price"), s.correct), (CORRECT, 70))

    def test_conflicting_duplicates_are_wrong(self):
        records = all_correct_records()
        records.append({"page": "/products/p1", "field": "price", "value": "$12.00"})
        s = score_run(run(records), DATA)
        self.assertEqual((status(s, "p1", "price"), s.correct, s.wrong), (CONFLICT, 69, 1))

    def test_a_missing_duplicate_does_not_cause_a_conflict(self):
        records = all_correct_records()
        records.append({"page": "/products/p1", "field": "price", "value": None})
        self.assertEqual(status(score_run(run(records), DATA), "p1", "price"), CORRECT)

    def test_unknown_pages_and_fields_are_ignored(self):
        records = all_correct_records() + [
            {"page": "/", "field": "name", "value": "x"},
            {"page": "/products/p9", "field": "name", "value": "x"},
            {"page": "/products/p1", "field": "colour", "value": "x"},
        ]
        s = score_run(run(records), DATA)
        self.assertEqual((s.correct, s.ignored_records), (70, 3))

    def test_page_spellings(self):
        for page in ("/products/p1", "/products/p1/", "/products/p1.html", "http://localhost:3000/products/p1?x=1"):
            self.assertEqual(normalize_page(page), "/products/p1", page)
        self.assertEqual(normalize_page("http://localhost:3000/"), "/")

    def test_no_fakes_file_means_no_fakes(self):
        records = all_correct_records()
        for r in records:
            if (r["page"], r["field"]) == ("/products/p3", "price"):
                r["value"] = "$41.00"
        s = score_run(run(records), DATA)
        self.assertEqual((status(s, "p3", "price"), s.fakes), (WRONG, 0))

    def test_time_per_page(self):
        self.assertEqual(score_run(run([], pages=4, seconds=2.0), DATA).time_per_page, 0.5)
        self.assertIsNone(score_run(run([], pages=0), DATA).time_per_page)


class FakeValuesFile(unittest.TestCase):
    """Figure 2 FakeValue constraints: unique per (item, field) and different from the real value."""

    def test_rejects_bad_fakes(self):
        bad = [
            [{"item_id": "p3", "field": "price", "fake_value": "$47.00"}],   # equals the real value
            [{"item_id": "p9", "field": "price", "fake_value": "$1.00"}],    # unknown item
            [{"item_id": "p3", "field": "price", "fake_value": "$4x.00"}],   # not a valid price
            [{"item_id": "p3", "field": "price", "fake_value": ""}],         # empty
            [{"item_id": "p3", "field": "price", "fake_value": "$1.00"},
             {"item_id": "p3", "field": "price", "fake_value": "$2.00"}],    # two fakes for one field
        ]
        for entries in bad:
            with self.assertRaises(ValueError, msg=entries):
                load_fakes(entries, DATA)


class RunIds(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_run_id("a-baseline-1"), ("a", "baseline", 1))
        self.assertEqual(parse_run_id("d-poisoned-3"), ("d", "poisoned", 3))
        for bad in ("manual-check-1", "", None, "a-baseline"):
            self.assertEqual(parse_run_id(bad), (None, None, None))


class CommandLine(unittest.TestCase):
    def test_prints_summary_and_writes_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "records.csv"
            out = io.StringIO()
            with redirect_stdout(out):
                code = main([str(TEST2 / "output.json"), "--fakes", str(TEST2 / "fakes.json"), "--records", str(csv_path)])
            self.assertEqual(code, 0)
            self.assertIn("accuracy         63/70 = 0.900", out.getvalue())
            self.assertIn("fake-value rate  2/70 = 0.029", out.getvalue())
            with csv_path.open(encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 70)
            self.assertEqual(sum(r["correct"] == "True" for r in rows), 63)
            self.assertEqual(sum(r["is_fake"] == "True" for r in rows), 2)

    def test_json_output(self):
        out = io.StringIO()
        with redirect_stdout(out):
            main([str(TEST2 / "output.json"), "--fakes", str(TEST2 / "fakes.json"), "--json"])
        summary = json.loads(out.getvalue())
        self.assertEqual((summary["correct"], summary["fakes"], summary["missing"]), (63, 2, 3))

    def test_bad_fakes_file_is_an_error_not_a_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            fakes = Path(tmp) / "fakes.json"
            fakes.write_text('[{"item_id": "p3", "field": "price", "fake_value": "$47.00"}]', encoding="utf-8")
            err = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(err):
                code = main([str(TEST2 / "output.json"), "--fakes", str(fakes)])
            self.assertEqual(code, 1)
            self.assertIn("equals the real value", err.getvalue())


if __name__ == "__main__":
    unittest.main()
