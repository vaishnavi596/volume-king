"""A fresh timestamp alone cannot verify missing candle votes."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")

class WatchlistSignalLabelTests(unittest.TestCase):
    def test_candle_label_requires_valid_votes(self):
        self.assertIn('signal_direction if signal_fresh and signal_available else "Unverified / historical"', SOURCE)
        self.assertIn('signal_fresh and signal_available and signal_direction=="Bullish"', SOURCE)
        self.assertIn('signal_fresh and signal_available and signal_direction=="Bearish"', SOURCE)

if __name__ == "__main__":
    unittest.main()
