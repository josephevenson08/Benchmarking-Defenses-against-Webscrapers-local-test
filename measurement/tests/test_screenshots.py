"""Checks for measurement/screenshots.py that need no browser.

Run with: python -m unittest discover -s measurement/tests -t .
"""

import json
import tempfile
import unittest
from pathlib import Path

from measurement.screenshots import load_pages, png_name


class PngNameTest(unittest.TestCase):
    def test_names_follow_the_page_path(self):
        self.assertEqual(png_name("/"), "index.png")
        self.assertEqual(png_name("/products/"), "products.png")
        self.assertEqual(png_name("/products/p1"), "products-p1.png")
        self.assertEqual(png_name("/articles/a2"), "articles-a2.png")


class LoadPagesTest(unittest.TestCase):
    def test_reads_the_page_list_from_the_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            pages = [{"path": "/", "file": "index.html", "type": "home"}]
            Path(tmp, "shuffled.manifest.json").write_text(json.dumps({"pages": pages}), encoding="utf-8")
            self.assertEqual(load_pages("shuffled", tmp), pages)

    def test_missing_manifest_says_to_generate(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit) as caught:
                load_pages("shuffled", tmp)
            self.assertIn("npm run generate -- shuffled", str(caught.exception))

    def test_old_manifest_without_file_names_says_to_regenerate(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "baseline.manifest.json").write_text(json.dumps({"pages": [{"path": "/"}]}), encoding="utf-8")
            with self.assertRaises(SystemExit) as caught:
                load_pages("baseline", tmp)
            self.assertIn("older generator", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
