"""Foreground interruptions preserve ranking and disclose incomplete scan coverage."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")

class DhanForegroundBoundaryTests(unittest.TestCase):
    def test_before_first_history_call(self):
        self.assertIn('Dhan history waiting for foreground • "+str(len(symbols))+" symbols not attempted', SOURCE)
        self.assertIn('Avoid even the first rate-sensitive history request', SOURCE)

    def test_after_partial_history(self):
        self.assertIn('Dhan historical scan paused in background • "+str(max(0,len(symbols)-market_completed[0]))+" symbols not attempted • last ranking retained', SOURCE)
        self.assertIn('last_scanned_generation=None', SOURCE)

if __name__ == "__main__":
    unittest.main()
