"""Checks for measurement/false_positive.py's counting (no browser needed).

Run with: python -m unittest discover -s measurement/tests -t .
"""
import unittest

from measurement import false_positive as fp


def line(run_id, path, second, ms=5.0, hit=False):
    return {"run_id": run_id, "path": path, "timestamp": f"2026-11-27T12:00:{second:02d}.000Z", "response_ms": ms,
            "honeypot_hit": hit}


class SessionResultTest(unittest.TestCase):
    def test_trap_hits_and_maze_time_come_from_the_log(self):
        entries = [line("human-tarpit-1", "/", 0), line("human-tarpit-1", "/maze/start", 1, 2000.0),
                   line("human-tarpit-1", "/maze/abc", 4, 2000.0), line("other", "/trap", 5, hit=True)]
        r = fp.session_result(entries, "human-tarpit-1", "/trap")
        self.assertEqual((r["requests"], r["trap_hits"], r["maze_pages"]), (3, 0, 2))
        self.assertAlmostEqual(r["maze_seconds"], 3.0 + 2.0)

    def test_a_trap_request_counts_as_caught(self):
        r = fp.session_result([line("human-honeypot-1", "/", 0), line("human-honeypot-1", "/trap", 2, hit=True)],
                              "human-honeypot-1", "/trap")
        self.assertEqual(r["trap_hits"], 1)


if __name__ == "__main__":
    unittest.main()
