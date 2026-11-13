"""Malformed watchlist signal cache rows must not crash fill_watch."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")

class WatchlistSignalCacheTests(unittest.TestCase):
    def test_normalize_signal_row_before_get(self):
        self.assertIn('signal_row=watch_signal_cache.get(sym,{})\n            if not isinstance(signal_row,dict):signal_row={}\n            signal_counts=signal_percentages(signal_row)', SOURCE)

if __name__ == "__main__":
    unittest.main()
