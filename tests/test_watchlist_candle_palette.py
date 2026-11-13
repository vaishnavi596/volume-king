"""Regression guard: stale and historical candle directions must remain muted."""
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")

class WatchlistCandlePaletteTests(unittest.TestCase):
    def test_fresh_bullish_bearish_are_colored(self):
        self.assertIn('GREEN if signal_fresh and signal_available and signal_direction=="Bullish"', SOURCE)
        self.assertIn('RED if signal_fresh and signal_available and signal_direction=="Bearish"', SOURCE)

    def test_unverified_historical_are_muted(self):
        self.assertIn('else "Unverified / historical"),11,', SOURCE)
        self.assertIn('signal_direction=="Bearish" else MUTED)', SOURCE)
        self.assertIn('and not signal_row.get("historical") and regular_hours()', SOURCE)

if __name__ == "__main__":
    unittest.main()
