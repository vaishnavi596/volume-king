"""Watchlist live direction filters must exclude historical or stale signals."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")

class WatchlistFreshFilterTests(unittest.TestCase):
    def test_direction_requires_fresh_and_matching_source(self):
        self.assertIn('if signal_available and signal_fresh else "Neutral"', SOURCE)
        self.assertIn('if watch_filter[0]!="All" and watch_filter[0]!=signal_direction:continue', SOURCE)
        self.assertIn('and not signal_row.get("historical") and regular_hours()', SOURCE)

if __name__ == "__main__":
    unittest.main()
