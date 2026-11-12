"""Offline safety checks for the read-only Dhan transport."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from server_feed import ServerDhanReadOnly, FeedError


class DhanAdapterTests(unittest.TestCase):
    def test_rejects_http_and_credentials_in_url(self):
        adapter = ServerDhanReadOnly()
        for url in ("http://example.com", "https://user:pass@example.com",
                    "https://example.com/path", "https://example.com?token=x"):
            with self.subTest(url=url), self.assertRaises(FeedError):
                adapter.connect(url, "not-a-secret")
            self.assertFalse(adapter.connected)

    def test_verified_symbol_only(self):
        adapter = ServerDhanReadOnly()
        adapter._origin = "https://example.com"
        adapter._pairing_key = "temporary"
        with self.assertRaises(FeedError):
            adapter.quote("RELIANCE")
        with self.assertRaises(FeedError):
            adapter.intraday("BANKNIFTY", 5, "2026-11-01", "2026-11-02")

    def test_batch_rejects_conflicting_availability(self):
        adapter = ServerDhanReadOnly()
        adapter._origin = "https://example.com"
        adapter._pairing_key = "temporary"
        response = {"source": "dhan", "live_orders_enabled": False,
                    "quotes": {"RELIANCE": 1200.0}, "unavailable": ["RELIANCE"]}
        with patch.object(adapter, "_call", return_value=response):
            with self.assertRaises(FeedError):
                adapter.batch_quotes()

    def test_batch_rejects_missing_unavailable_list(self):
        adapter = ServerDhanReadOnly()
        adapter._origin = "https://example.com"
        adapter._pairing_key = "temporary"
        response = {"source": "dhan", "live_orders_enabled": False,
                    "quotes": {"RELIANCE": 1200.0}}
        with patch.object(adapter, "_call", return_value=response):
            with self.assertRaises(FeedError):
                adapter.batch_quotes()

    def test_quote_timestamp_not_fabricated(self):
        adapter = ServerDhanReadOnly()
        adapter._origin = "https://example.com"
        adapter._pairing_key = "temporary"
        with patch.object(adapter, "_call", return_value={
            "live_orders_enabled": False, "source": "dhan",
            "symbol": "NIFTY", "ltp": 25030.35
        }):
            quote = adapter.quote("NIFTY")
        self.assertIsNone(quote["quote_timestamp"])
        self.assertEqual(quote["source"], "Dhan")

    def test_connect_requires_valid_status_and_quote(self):
        adapter = ServerDhanReadOnly()
        with patch.object(adapter, "_call", side_effect=[
            {"live_orders_enabled": False, "market_data_configured": True},
            {"live_orders_enabled": False, "source": "dhan",
             "symbol": "NIFTY", "ltp": 25030.35},
        ]):
            result = adapter.connect("https://example.com", "temporary")
        self.assertTrue(adapter.connected)
        self.assertEqual(result["price"], 25030.35)
        adapter.disconnect()
        self.assertFalse(adapter.connected)

    def test_connect_clears_credentials_after_failure(self):
        adapter = ServerDhanReadOnly()
        with patch.object(adapter, "_call", return_value={
            "live_orders_enabled": False, "market_data_configured": False
        }):
            with self.assertRaises(FeedError):
                adapter.connect("https://example.com", "temporary")
        self.assertFalse(adapter.connected)


if __name__ == "__main__":
    unittest.main()
