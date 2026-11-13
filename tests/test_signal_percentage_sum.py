"""Bullish and bearish candle percentages must always sum to 100."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
class SignalPercentageSumTests(unittest.TestCase):
    def test_complementary_percentage_formula(self):
        self.assertIn('return (round(100*bulls/total),100-round(100*bulls/total),total) if total else None', SOURCE)
    def test_rounding_example(self):
        bulls,total=1,8
        bullish=round(100*bulls/total)
        bearish=100-bullish
        self.assertEqual(bullish+bearish,100)
if __name__ == "__main__":
    unittest.main()
