"""Guard against chart-triggered duplicate NIFTY LTP requests.

The dedicated index batch poller owns index LTP recovery. A historical
chart must reuse its same-provider cached price and never fan out requests.
"""
from pathlib import Path
import unittest

MAIN = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")


class NiftyChartLtpIsolationTests(unittest.TestCase):
    def test_historical_chart_reuses_index_quote_without_independent_ltp(self):
        start = MAIN.index("    def fetch_market_data_uncached(")
        end = MAIN.index("    def timeframe_spec(", start)
        block = MAIN[start:end]
        self.assertIn('saved_index=quotes.get("NIFTY")', block)
        self.assertIn('saved_index.get("source")=="Dhan"', block)
        self.assertIn('math.isfinite(saved_index["price"])', block)
        self.assertNotIn('dhan_feed.quote(ticker)', block)
        self.assertIn('"price":quote["price"] if quote else None', block)
        self.assertIn('"live_verified":False', block)


if __name__ == "__main__":
    unittest.main()
