"""Guard Dhan chart equity quote path against per-symbol LTP regressions."""
import unittest
from pathlib import Path


class ChartQuoteSourceTests(unittest.TestCase):
    def test_equities_use_oracle_batch_snapshot_and_index_uses_ltp(self):
        text=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        start=text.index("    def fetch_market_data_uncached(")
        end=text.index("            elif angel_feed.connected:",start)
        chart=text[start:end]
        self.assertIn('if ticker=="NIFTY":\n                            quote=dhan_feed.quote(ticker)',chart)
        self.assertIn('else:\n                            quote=dhan_feed.batch_quotes().get(ticker)',chart)
        self.assertIn('"price":quote["price"] if quote else None',chart)
        self.assertIn('"historical_unverified"',chart)


if __name__ == "__main__":
    unittest.main()
