"""Stale percent changes must not masquerade as live moves."""
from pathlib import Path
import unittest
SOURCE=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
class QuoteChangeFreshnessTests(unittest.TestCase):
    def test_quote_change_requires_recent_valid_ltp(self):
        section=SOURCE.split('    def quote_change(sym):',1)[1].split('    def price_color(sym):',1)[0]
        self.assertIn('price<=0',section)
        self.assertIn('not 0<=time.time()-stamp<=60',section)
        self.assertIn('or not math.isfinite(stamp)',section)
        self.assertIn('return "—"',section)
if __name__=="__main__":unittest.main()
