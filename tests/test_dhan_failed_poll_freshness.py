"""Failed or interrupted Dhan polls must not preserve a live freshness claim."""
from pathlib import Path
import unittest
SOURCE=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
class DhanFailedPollFreshnessTests(unittest.TestCase):
    def setUp(self):
        self.body=SOURCE.split('    async def refresh_watch_batch():',1)[1].split('    async def dhan_quote_poll():',1)[0]
        self.failure=self.body.split('        except Exception as exc:',1)[1]
    def test_failure_downgrades_before_background_return(self):
        self.assertLess(self.failure.index('quotes[ticker]=dict(old,freshness="unverified",live_verified=False)'),
                        self.failure.index('if not app_active[0]:'))
    def test_only_valid_dhan_prices_are_retained(self):
        self.assertIn('old.get("source")=="Dhan"',self.failure)
        self.assertIn('math.isfinite(old["price"])',self.failure)
        self.assertIn('not isinstance(old.get("price"),bool)',self.failure)
    def test_failure_does_not_blank_quotes(self):
        self.assertNotIn('quotes.clear()',self.failure)
if __name__=="__main__":
    unittest.main()
