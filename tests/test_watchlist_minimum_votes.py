"""Watchlist directional labels require enough votes for agreement."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
class WatchlistMinimumVotesTests(unittest.TestCase):
    def test_verified_direction_requires_two_votes(self):
        self.assertIn('and signal_counts is not None and signal_counts[2]>=2)', SOURCE)
        self.assertIn('if total<2:return note("Signal agreement insufficient', SOURCE)
if __name__ == "__main__":
    unittest.main()
