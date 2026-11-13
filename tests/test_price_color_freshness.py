"""Price movement colors must not imply a live move from stale quotes."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
class PriceColorFreshnessTests(unittest.TestCase):
    def test_price_color_requires_recent_valid_quote(self):
        section=SOURCE.split('    def price_color(sym):',1)[1].split('    def tiny_chart(',1)[0]
        self.assertIn('q=None if dhan_offline() else quotes.get(sym)',section)
        self.assertIn('q.get("source")!=expected',section)
        self.assertIn('price<=0',section)
        self.assertIn('not 0<=time.time()-stamp<=60',section)
        self.assertIn('return MUTED',section)
if __name__ == "__main__":
    unittest.main()
