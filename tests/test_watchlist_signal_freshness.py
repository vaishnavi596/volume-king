"""Fresh watchlist signal labels require trustworthy timestamp types and bounds."""
from pathlib import Path
import unittest

SRC = Path(__file__).resolve().parents[1] / "src" / "main.py"


class WatchlistSignalFreshnessTests(unittest.TestCase):
    def test_fresh_signal_rejects_bool_nan_infinity_and_nonpositive_time(self):
        source = SRC.read_text(encoding="utf-8")
        body = source.split("    def fill_watch(", 1)[1].split("    def ", 1)[0]
        fresh = body.split("signal_fresh=(", 1)[1].split("signal_available=", 1)[0]
        self.assertIn("not isinstance(signal_stamp,bool)", fresh)
        self.assertIn("math.isfinite(signal_stamp) and signal_stamp>0", fresh)
        self.assertIn('0<=datetime.now(timezone.utc).timestamp()-signal_stamp<=timeframe_spec("5m")["fresh_seconds"]', fresh)


if __name__ == "__main__":
    unittest.main()
