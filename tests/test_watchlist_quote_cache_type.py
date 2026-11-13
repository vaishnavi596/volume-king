"""Malformed quote cache rows must not crash Watchlist."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")

class WatchlistQuoteCacheTests(unittest.TestCase):
    def test_normalize_quote_row_before_source_lookup(self):
        self.assertIn('quote_row=quotes.get(sym) or {}\n            if not isinstance(quote_row,dict):quote_row={}\n            quote_source=quote_row.get("source")', SOURCE)

if __name__ == "__main__":
    unittest.main()
