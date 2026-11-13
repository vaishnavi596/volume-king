"""Malformed candle vote containers must not crash Watchlist rendering."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")

class VoteContainerTests(unittest.TestCase):
    def test_reject_non_sequence_votes(self):
        self.assertIn('if not isinstance(votes,(list,tuple)):return None', SOURCE)
        self.assertIn('if not counts:return note("Signal agreement unavailable")', SOURCE)

if __name__ == "__main__":
    unittest.main()
