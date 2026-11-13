"""Regression guard for partial Dhan batch quote freshness."""
from pathlib import Path
import unittest
SOURCE=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
class DhanPartialBatchFreshnessTests(unittest.TestCase):
    def setUp(self):
        self.body=SOURCE.split('    async def refresh_watch_batch():',1)[1].split('    async def dhan_quote_poll():',1)[0]
    def test_missing_and_invalid_quotes_downgraded(self):
        self.assertIn('if not valid and (old:=quotes.get(ticker))',self.body)
        self.assertIn('dict(old,freshness="unverified",live_verified=False)',self.body)
    def test_validity_requires_dhan_finite_price(self):
        self.assertIn('snapshot.get("source")=="Dhan"',self.body)
        self.assertIn('math.isfinite(snapshot["price"])',self.body)
    def test_last_price_is_not_blank(self):
        self.assertNotIn('quotes.pop(ticker)',self.body)
if __name__=="__main__":
    unittest.main()
