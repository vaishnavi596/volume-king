import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from v3_breadth import breadth, breadth_text


class BreadthTests(unittest.TestCase):
    def test_counts_and_lean(self):
        b = breadth([1.0] * 35 + [-1.0] * 10 + [0.0] * 6 + [None, float("nan")])
        self.assertEqual((b["up"], b["down"], b["flat"], b["total"]), (35, 10, 6, 51))
        self.assertIn("bullish", breadth_text(b)); self.assertIn("not voted", breadth_text(b))

    def test_too_few_is_none(self):
        self.assertIsNone(breadth([1.0] * 5)); self.assertEqual(breadth_text(None), "Breadth: n/a")

    def test_mixed(self):
        self.assertIn("mixed", breadth_text(breadth([1.0] * 25 + [-1.0] * 25)))
