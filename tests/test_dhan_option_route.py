"""Option-chain route must fail closed on unverified underlying and bad auth."""
import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.server import create_app
from backend.dhan_feed import DhanRateLimitError


class DhanOptionRouteTests(unittest.TestCase):
    def setUp(self):
        self.key = "k" * 40
        self.client = TestClient(create_app(pairing_key=self.key))

    def test_auth_and_mapping_reject_before_dhan_request(self):
        payload = {"symbol": "BANKNIFTY", "expiry": "2099-12-31"}
        response = self.client.post("/dhan/option-chain", json=payload)
        self.assertEqual(response.status_code, 403)
        response = self.client.post("/dhan/option-chain", json=payload,
                                    headers={"X-BotKing-Key": self.key})
        self.assertEqual(response.status_code, 422)

    def test_success_response_is_explicitly_unverified_and_read_only(self):
        chain = {"status": "success", "data": {"oc": {
            "100": {"ce": {"oi": 10}, "pe": {"oi": 5}},
            "110": {"ce": {"oi": 5}, "pe": {"oi": 10}},
        }}}
        with patch.dict(os.environ, {"DHAN_CLIENT_ID": "test-client"}):
            with patch("backend.server.dhan_market_token", return_value="test-token"):
                with patch("backend.server.DhanFeed.option_chain", return_value=chain) as feed:
                    response = self.client.post("/dhan/option-chain",
                        json={"symbol": "NIFTY", "expiry": "2099-12-31"},
                        headers={"X-BotKing-Key": self.key})
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["source"], "dhan")
        self.assertEqual(result["pcr"], 1.0)
        self.assertEqual(result["freshness"], "unverified")
        self.assertFalse(result["signal_eligible"])
        self.assertFalse(result["live_orders_enabled"])
        feed.assert_called_once_with("IDX_I", 13, "2099-12-31")

    def test_provider_rate_limit_returns_retry_after_without_fallback(self):
        with patch.dict(os.environ, {"DHAN_CLIENT_ID": "test-client"}):
            with patch("backend.server.dhan_market_token", return_value="test-token"):
                with patch("backend.server.DhanFeed.option_chain",
                           side_effect=DhanRateLimitError("cooldown")):
                    response = self.client.post("/dhan/option-chain",
                        json={"symbol": "NIFTY", "expiry": "2099-12-31"},
                        headers={"X-BotKing-Key": self.key})
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers["retry-after"], "30")

    def test_incomplete_chain_returns_502_without_fabricated_metrics(self):
        with patch.dict(os.environ, {"DHAN_CLIENT_ID": "test-client"}):
            with patch("backend.server.dhan_market_token", return_value="test-token"):
                with patch("backend.server.DhanFeed.option_chain",
                           return_value={"status": "success", "data": {"oc": {}}}):
                    response = self.client.post("/dhan/option-chain",
                        json={"symbol": "NIFTY", "expiry": "2099-12-31"},
                        headers={"X-BotKing-Key": self.key})
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("pcr", response.json())

    def test_past_expiry_rejected_for_mapped_nifty(self):
        response = self.client.post("/dhan/option-chain",
                                    json={"symbol": "NIFTY", "expiry": "2020-01-01"},
                                    headers={"X-BotKing-Key": self.key})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
