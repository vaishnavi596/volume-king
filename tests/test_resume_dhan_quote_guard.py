"""Resume candle fetch must not erase the last valid Dhan batch LTP."""
from pathlib import Path
import unittest
SOURCE=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
class ResumeDhanQuoteGuardTests(unittest.TestCase):
    def setUp(self):
        self.body=SOURCE.split('    async def refresh_after_resume():',1)[1].split('    def lifecycle_changed(e):',1)[0]
    def test_last_valid_dhan_price_is_preserved(self):
        self.assertIn('previous.get("source")=="Dhan"',self.body)
        self.assertIn('math.isfinite(previous["price"])',self.body)
        self.assertIn('quotes[sym]=dict(previous,bars=data.get("bars"',self.body)
    def test_resume_downgrades_freshness(self):
        self.assertIn('freshness="unverified"',self.body)
    def test_non_dhan_or_missing_previous_quote_uses_result(self):
        self.assertIn('else:\n                        quotes[sym]=data',self.body)
if __name__=="__main__":
    unittest.main()
