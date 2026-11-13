"""A stale quote change cannot be labeled as current price direction."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
class WatchlistDirectionFreshnessTests(unittest.TestCase):
    def test_direction_requires_recent_quote(self):
        self.assertIn('and quote_age is not None and 0<=quote_age<=60', SOURCE)
        self.assertLess(SOURCE.index('quote_age=time.time()-quote_row["fetched_at"]'),SOURCE.index('valid_change=('))
if __name__ == "__main__":
    unittest.main()
