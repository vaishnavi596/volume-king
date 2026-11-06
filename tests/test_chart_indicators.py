"""Offline chart validation and indicator tests."""
import unittest
from src.chart_indicators import chart_indicators


def candles(n=80, step=1):
    return [[1700000000 + i*300, 100 + i*step, 101 + i*step,
             99 + i*step, 100.5 + i*step, 1000] for i in range(n)]


class ChartIndicatorTests(unittest.TestCase):
    def test_rising_market_has_calculated_levels(self):
        r = chart_indicators(candles())
        self.assertEqual(r["status"], "AVAILABLE")
        self.assertEqual(r["bias"], "BULLISH")
        self.assertLess(r["support"], r["price"])
        self.assertGreater(r["atr14"], 0)

    def test_falling_market(self):
        r = chart_indicators(candles(step=-0.5))
        self.assertEqual(r["status"], "AVAILABLE")
        self.assertEqual(r["bias"], "BEARISH")

    def test_insufficient_candles_not_a_signal(self):
        self.assertEqual(chart_indicators(candles(10))["status"], "UNAVAILABLE")

    def test_bad_ohlc_not_a_signal(self):
        bars = candles()
        for bar in bars:
            bar[2] = bar[3] - 1
        self.assertEqual(chart_indicators(bars)["status"], "UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
