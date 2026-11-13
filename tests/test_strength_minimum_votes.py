"""A single candle vote is insufficient for agreement strength."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
class StrengthMinimumVotesTests(unittest.TestCase):
    def test_single_vote_not_shown_as_agreement(self):
        self.assertIn('if total<2:return note("Signal agreement insufficient • fewer than 2 votes")', SOURCE)
        self.assertIn('bull,bear,total=counts', SOURCE)
if __name__ == "__main__":
    unittest.main()
