"""Offline unittest checks for the Oracle Dhan option gateway."""
import unittest
from unittest.mock import patch
from market_feed import FeedError
from server_feed import ServerDhanReadOnly


class DhanOptionGatewayTests(unittest.TestCase):
    def setUp(self):
        self.client = ServerDhanReadOnly()
        self.client._origin = "https://example.org"
        self.client._pairing_key = "test-only"

    def test_broker_listed_expiries(self):
        with patch.object(self.client, "_call", return_value={
            "source": "dhan", "symbol": "NIFTY",
            "expiries": ["2026-11-17", "2026-11-23"],
            "live_orders_enabled": False,
        }) as call:
            self.assertEqual(self.client.option_expiries("NIFTY"),
                             ["2026-11-17", "2026-11-23"])
            call.assert_called_once_with("/dhan/option-expiries", {"symbol": "NIFTY"})
        with self.assertRaises(FeedError):
            self.client.option_expiries("BANKNIFTY")

    def test_invalid_expiry_lists(self):
        for dates in ([], ["2026-11-23", "2026-11-17"],
                      ["2026-11-17", "2026-11-17"], ["2026-11-19", "not-a-date"]):
            with self.subTest(dates=dates), patch.object(self.client, "_call", return_value={
                "source": "dhan", "symbol": "NIFTY", "expiries": dates,
            }):
                with self.assertRaises(FeedError):
                    self.client.option_expiries("NIFTY")

    def test_metrics_read_only(self):
        payload = {
            "source": "dhan", "symbol": "NIFTY", "expiry": "2026-11-17",
            "pcr": 0.83049, "max_pain": 25100.0, "freshness": "unverified",
            "signal_eligible": False, "live_orders_enabled": False,
        }
        with patch.object(self.client, "_call", return_value=payload) as call:
            self.assertEqual(self.client.option_chain_metrics("NIFTY", "2026-11-17")["pcr"], 0.83049)
            call.assert_called_once_with("/dhan/option-chain", {
                "symbol": "NIFTY", "expiry": "2026-11-17",
            })
        for field, value in (("signal_eligible", True), ("freshness", "exchange_verified"),
                             ("pcr", float("nan")), ("max_pain", None)):
            with self.subTest(field=field), patch.object(
                self.client, "_call", return_value={**payload, field: value}
            ):
                with self.assertRaises(FeedError):
                    self.client.option_chain_metrics("NIFTY", "2026-11-17")

    def test_invalid_requests_fail_before_network(self):
        with patch.object(self.client, "_call", side_effect=AssertionError("network called")):
            with self.assertRaises(FeedError):
                self.client.option_chain_metrics("BANKNIFTY", "2026-11-17")
            with self.assertRaises(FeedError):
                self.client.option_chain_metrics("NIFTY", "not-a-date")


if __name__ == "__main__":
    unittest.main()
