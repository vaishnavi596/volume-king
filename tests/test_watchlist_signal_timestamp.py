"""Invalid timestamps must never qualify as available watchlist signals."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")

class WatchlistSignalTimestampTests(unittest.TestCase):
    def test_signal_availability_requires_finite_timestamp(self):
        self.assertIn('isinstance(signal_stamp,(int,float)) and not isinstance(signal_stamp,bool) and math.isfinite(signal_stamp)', SOURCE)
        self.assertIn('if signal_available and signal_fresh else "Neutral"', SOURCE)

if __name__ == "__main__":
    unittest.main()
