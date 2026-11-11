"""Offline scanner candle safety regression."""
import math, sys, unittest
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scanner_engine import analyze, rank_candidates

def candles():
    start = int(datetime.now(timezone.utc).timestamp()) - 35 * 300
    return [[start + i * 300, 100., 102., 99., 101., 1000.] for i in range(35)]

class ScannerSafetyTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(analyze(candles())["count"], 35)
    def test_duplicate_timestamp(self):
        b = candles(); b[-1][0] = b[-2][0]
        r = analyze(b)
        self.assertEqual(r["bias"], "WAIT")
        self.assertIsNone(r["timestamp"])
    def test_reversed_timestamp(self):
        b = candles(); b[-1][0] = b[-2][0] - 1
        self.assertEqual(analyze(b)["bias"], "WAIT")
    def test_impossible_ohlc(self):
        b = candles(); b[-1][2] = 90.
        self.assertEqual(analyze(b)["count"], 34)
    def test_nan(self):
        b = candles(); b[-1][4] = math.nan
        self.assertEqual(analyze(b)["count"], 34)
    def test_insufficient_ranking(self):
        r = {"bias":"BULLISH","timestamp":datetime.now(timezone.utc).timestamp(),"count":5,"score":99,"votes":[]}
        self.assertEqual(rank_candidates({"ABC":r}), [])

if __name__ == "__main__":
    unittest.main()
