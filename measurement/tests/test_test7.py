"""Checks for measurement/test7.py: the test site and the pass/fail rules, without running a scraper.

Run with: python -m unittest discover -s measurement/tests -t .
"""

import time
import unittest
import urllib.error
import urllib.request

from measurement import test7 as t7

GOOD = [{"path": "/", "status": 200, "error": None}, {"path": "/t7/a", "status": 200, "error": None},
        {"path": "/t7/missing", "status": 404, "error": None}, {"path": "/t7/slow", "status": None, "error": "timeout"},
        {"path": "/t7/b", "status": 200, "error": None}]


class RulesTest(unittest.TestCase):
    def test_a_good_crawl_passes_every_check(self):
        self.assertTrue(all(t7.check_full_crawl(GOOD).values()))
        self.assertTrue(all(t7.check_capped_crawl(GOOD[:3], 3).values()))

    def test_a_loop_is_caught(self):
        looped = GOOD + [{"path": "/t7/a", "status": 200, "error": None}]
        checks = t7.check_full_crawl(looped)
        self.assertFalse(checks["no page visited twice (no loop)"])

    def test_waiting_out_the_slow_page_is_not_a_timeout(self):
        waited = [dict(p, status=200, error=None) if p["path"] == "/t7/slow" else p for p in GOOD]
        self.assertFalse(t7.check_full_crawl(waited)["timeout recorded"])

    def test_stopping_at_the_timeout_is_caught(self):
        stopped = GOOD[:4]
        checks = t7.check_full_crawl(stopped)
        self.assertFalse(checks["kept going after the timeout"])
        self.assertFalse(checks["every page visited"])

    def test_skipping_the_404_is_caught(self):
        self.assertFalse(t7.check_full_crawl([p for p in GOOD if p["path"] != "/t7/missing"])["404 recorded"])

    def test_going_past_the_cap_is_caught(self):
        self.assertFalse(t7.check_capped_crawl(GOOD[:4], 3)["stopped at the page cap (3)"])


class SiteTest(unittest.TestCase):
    def setUp(self):
        self.server = t7.serve_site(slow_seconds=0.3)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_pages_link_as_described(self):
        home = urllib.request.urlopen(self.base + "/").read().decode()
        for href in ("/t7/a", "/t7/missing", "/t7/slow"):
            self.assertIn(f'href="{href}"', home)
        self.assertIn('href="/"', urllib.request.urlopen(self.base + "/t7/b").read().decode())

    def test_missing_is_404_and_robots_allows_all(self):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(self.base + "/t7/missing")
        self.assertEqual(caught.exception.code, 404)
        self.assertIn("Disallow:\n", urllib.request.urlopen(self.base + "/robots.txt").read().decode())

    def test_slow_page_answers_late(self):
        start = time.perf_counter()
        urllib.request.urlopen(self.base + "/t7/slow").read()
        self.assertGreaterEqual(time.perf_counter() - start, 0.3)


if __name__ == "__main__":
    unittest.main()
