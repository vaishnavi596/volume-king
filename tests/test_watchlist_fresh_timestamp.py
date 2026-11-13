"""Watchlist candle freshness must safely reject NaN and infinite timestamps."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")

class WatchlistFreshTimestampTests(unittest.TestCase):
    def test_freshness_rejects_nonfinite_timestamps(self):
        self.assertIn('and isinstance(signal_stamp,(int,float)) and math.isfinite(signal_stamp)\n                          and 0<=datetime.now(timezone.utc).timestamp()-signal_stamp', SOURCE)
        self.assertIn('if signal_available and signal_fresh else "Neutral"', SOURCE)

if __name__ == "__main__":
    unittest.main()
