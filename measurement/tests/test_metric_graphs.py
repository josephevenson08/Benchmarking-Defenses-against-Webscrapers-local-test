"""Checks for measurement/metric_graphs.py (run with: python -m unittest discover -s measurement/tests -t .)."""

import importlib.util
import tempfile
import unittest
from pathlib import Path


@unittest.skipUnless(importlib.util.find_spec("matplotlib"), "matplotlib not installed (pip install -r requirements.txt)")
class MetricGraphsTest(unittest.TestCase):
    def test_labels_never_show_minus_zero(self):
        from measurement import metric_graphs as mg
        self.assertEqual(mg.label("{:+.0f}", -0.2), "+0")
        self.assertEqual(mg.label("{:+.0f}", -7.0), "-7")
        self.assertEqual(mg.label("{:.1f}%", 94.28), "94.3%")

    def test_one_graph_per_metric_from_the_committed_results(self):
        import sys
        from unittest import mock
        from measurement import metric_graphs as mg
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            argv = ["metric_graphs.py", "--cells", str(root / "results/2026-11-20-results-all/cells.csv"),
                    "--cost", str(root / "results/2026-11-20-user-cost-full/cost.csv"), "--out", tmp]
            with mock.patch.object(sys, "argv", argv), mock.patch("builtins.print"):
                mg.main()
            written = sorted(p.name for p in Path(tmp).glob("*.png"))
        self.assertEqual(len(written), 10)
        self.assertIn("5-drop-in-recall.png", written)


if __name__ == "__main__":
    unittest.main()
