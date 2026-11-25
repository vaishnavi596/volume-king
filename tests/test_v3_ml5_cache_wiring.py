import pathlib
import unittest
SRC=(pathlib.Path(__file__).resolve().parents[1]/"src"/"main.py").read_text()
class ML5CacheWiringTests(unittest.TestCase):
    def test_timestamp_preserved_in_candle_and_scanner_paths(self):
        self.assertIn('"quote_timestamp":quote.get("quote_timestamp") if quote else None',SRC)
        self.assertIn('price=latest["price"],quote_timestamp=latest.get("quote_timestamp")',SRC)
        self.assertIn('not accept_newer_dhan_quote(previous_quote,data)',SRC)
        self.assertIn('if accept_newer_dhan_quote(old,snapshot):',SRC)
