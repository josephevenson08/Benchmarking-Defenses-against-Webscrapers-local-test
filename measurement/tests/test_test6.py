"""Checks for the log counting in measurement/test6.py (no server or browser needed).

Run with: python -m unittest discover -s measurement/tests -t .
"""

import unittest

from measurement.test6 import analyse_log, test6_passed

GOOD_LOG = [
    {"run_id": "test6", "path": "/trap", "honeypot_hit": True, "user_agent": "bench-test (run=test6)"},
    {"run_id": "test6", "path": "/products/p1", "honeypot_hit": False, "user_agent": "bench-test (run=test6)"},
    {"run_id": "unknown", "path": "/", "honeypot_hit": False, "user_agent": None},
    {"run_id": "test6-alive", "path": "/products/", "honeypot_hit": False, "user_agent": "bench-test (run=test6-alive)"},
]
OK = {"trap, run R": 200, "normal page, run R": 200, "no User-Agent": 200, "afterwards": 200}


class AnalyseLogTest(unittest.TestCase):
    def test_counts_the_expected_log_lines(self):
        counts = analyse_log(GOOD_LOG, "test6", "/trap", "/products/p1")
        self.assertEqual(counts, {
            "trap_lines_for_run": 1, "trap_hits_for_run": 1,
            "normal_lines_for_run": 1, "normal_hits_for_run": 0,
            "unknown_lines": 1, "unknown_without_user_agent": 1,
            "hits_for_other_runs": 0,
        })
        self.assertTrue(test6_passed(counts, OK, alive=True))

    def test_fails_when_the_trap_is_not_flagged(self):
        log = [dict(GOOD_LOG[0], honeypot_hit=False)] + GOOD_LOG[1:]
        self.assertFalse(test6_passed(analyse_log(log, "test6", "/trap", "/products/p1"), OK, alive=True))

    def test_fails_when_a_normal_page_is_flagged_or_the_run_id_is_lost(self):
        flagged = GOOD_LOG[:1] + [dict(GOOD_LOG[1], honeypot_hit=True)] + GOOD_LOG[2:]
        self.assertFalse(test6_passed(analyse_log(flagged, "test6", "/trap", "/products/p1"), OK, alive=True))
        lost = [dict(GOOD_LOG[0], run_id="unknown")] + GOOD_LOG[1:]
        self.assertFalse(test6_passed(analyse_log(lost, "test6", "/trap", "/products/p1"), OK, alive=True))

    def test_fails_when_the_server_went_down_or_a_request_failed(self):
        counts = analyse_log(GOOD_LOG, "test6", "/trap", "/products/p1")
        self.assertFalse(test6_passed(counts, OK, alive=False))
        self.assertFalse(test6_passed(counts, dict(OK, afterwards=500), alive=True))


if __name__ == "__main__":
    unittest.main()
