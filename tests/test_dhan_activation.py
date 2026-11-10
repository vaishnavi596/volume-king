"""Regression checks for Dhan read-only activation after verified LTP."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from server_feed import ServerDhanReadOnly
from market_feed import FeedError


class DhanActivationTests(unittest.TestCase):
    def test_uses_verified_quote_without_second_network_call(self):
        feed = ServerDhanReadOnly()
        quote = {"source": "dhan", "symbol": "NIFTY", "ltp": 25030.35,
                 "live_orders_enabled": False}
        with patch.object(feed, "_call", side_effect=AssertionError("duplicate request")):
            feed.activate_verified("https://example.org", "test-pairing-key", quote)
        self.assertTrue(feed.connected)
        feed.disconnect()
        self.assertFalse(feed.connected)

    def test_historical_activation_requires_real_read_only_candles(self):
        feed = ServerDhanReadOnly()
        candles = {"source": "dhan", "symbol": "RELIANCE",
                   "live_orders_enabled": False,
                   "freshness": "historical_unverified",
                   "bars": [[1762500000, 100.0, 102.0, 99.0, 101.0, 500]]}
        feed.activate_historical_verified("https://example.org", "test-pairing-key", candles)
        self.assertTrue(feed.connected)
        feed.disconnect()
        for bad in (dict(candles, bars=[]),
                    dict(candles, live_orders_enabled=True),
                    dict(candles, freshness="live"),
                    dict(candles, symbol="NIFTY")):
            with self.subTest(bad=bad):
                with self.assertRaises(FeedError):
                    feed.activate_historical_verified("https://example.org", "test-pairing-key", bad)
                self.assertFalse(feed.connected)

    def test_rejects_unverified_or_live_order_responses(self):
        for quote in (
            {"source": "dhan", "symbol": "NIFTY", "ltp": 25030.35,
             "live_orders_enabled": True},
            {"source": "dhan", "symbol": "NIFTY", "ltp": 0,
             "live_orders_enabled": False},
            {"source": "dhan", "symbol": "BANKNIFTY", "ltp": 25030.35,
             "live_orders_enabled": False},
        ):
            with self.subTest(quote=quote):
                feed = ServerDhanReadOnly()
                with self.assertRaises(FeedError):
                    feed.activate_verified("https://example.org", "test-pairing-key", quote)
                self.assertFalse(feed.connected)


if __name__ == "__main__":
    unittest.main()
