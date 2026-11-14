"""Malformed or future candle data must never generate scanner signals."""
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scanner_engine import analyze


class ScannerCandleIntegrity(unittest.TestCase):
    def test_malformed_candle_fails_closed(self):
        now = int(datetime.now(timezone.utc).timestamp())
        start = now - 50 * 300
        bars = [[start + i * 300, 100+i*.1, 101+i*.1,
                 99+i*.1, 100+i*.1, 1000] for i in range(40)]
        bars[18] = [start + 18*300, 100, 99, 101, 100, 1000]
        result = analyze(bars, ["EMA 9/21"], "5m")
        self.assertEqual(result["bias"], "WAIT")
        self.assertEqual(result["votes"], [])
        self.assertIsNone(result["timestamp"])
        self.assertEqual(result["reason"], "Invalid or future candle in series")

    def test_future_candle_fails_closed(self):
        now = int(datetime.now(timezone.utc).timestamp())
        start = now - 50 * 300
        bars = [[start + i*300, 100, 101, 99, 100, 1000]
                for i in range(40)]
        bars[-1][0] = now + 3600
        result = analyze(bars, ["MACD"], "5m")
        self.assertEqual(result["bias"], "WAIT")
        self.assertIsNone(result["timestamp"])


if __name__ == "__main__":
    unittest.main()
