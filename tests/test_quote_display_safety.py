"""Dhan quote UI preserves valid LTP while masking unsafe changes."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
class QuoteDisplaySafetyTests(unittest.TestCase):
    def test_cached_price_survives_disconnect(self):
        section=SOURCE.split('    def quote_price(sym):',1)[1].split('    def quote_change(sym):',1)[0]
        self.assertIn('q=quotes.get(sym)',section)
        self.assertIn('q.get("source")!=expected',section)
        self.assertIn('math.isfinite(v) and v>0',section)
    def test_change_is_masked_offline(self):
        section=SOURCE.split('    def quote_change(sym):',1)[1].split('    def price_color(sym):',1)[0]
        self.assertIn('q=None if dhan_offline() else quotes.get(sym)',section)
        self.assertIn('math.isfinite(v)',section)
if __name__ == "__main__":
    unittest.main()
