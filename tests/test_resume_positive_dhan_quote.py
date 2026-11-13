"""Regression: resume must not preserve invalid nonpositive Dhan prices."""
from pathlib import Path
import unittest
SOURCE=(Path(__file__).resolve().parents[1]/"src/main.py").read_text(encoding="utf-8")
RESUME=SOURCE.split("    async def refresh_after_resume():",1)[1].split("    def lifecycle_changed(e):",1)[0]
class ResumePriceValidityTests(unittest.TestCase):
    def test_retained_quote_requires_positive_finite_numeric_price(self):
        section=RESUME.split("previous_dhan_price=",1)[1].split("if previous_dhan_price:",1)[0]
        for guard in ('previous.get("source")=="Dhan"','not isinstance(previous.get("price"),bool)',
                      'math.isfinite(previous["price"])','previous["price"]>0'):
            self.assertIn(guard,section)
    def test_historical_candle_cannot_override_valid_dhan_quote(self):
        self.assertIn('quotes[sym]=dict(previous,bars=',RESUME)
        self.assertIn('freshness="unverified"',RESUME)
if __name__=="__main__":
    unittest.main()
