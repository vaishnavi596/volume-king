"""Boolean timestamps are not valid candle observation times."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
class WatchlistSignalBooleanTimestampTests(unittest.TestCase):
    def test_fresh_and_available_reject_boolean_timestamp(self):
        self.assertGreaterEqual(SOURCE.count('not isinstance(signal_stamp,bool) and math.isfinite(signal_stamp)'), 2)
if __name__ == "__main__":
    unittest.main()
