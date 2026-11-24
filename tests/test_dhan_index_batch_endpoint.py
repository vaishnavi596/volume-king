"""One-request Dhan index batch contract: auth, mapping, partial quotes, cooldown."""
import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from backend.server import create_app, DhanRateLimitError


KEY = "test-only-index-batch-pairing-key-32"


class IndexBatchEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app(pairing_key=KEY))
        self.headers = {"X-BotKing-Key": KEY}
        self.env = patch.dict(os.environ, {"DHAN_CLIENT_ID": "test-client"})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_requires_pairing_key_without_upstream_call(self):
        with patch("backend.server.DhanFeed", side_effect=AssertionError("upstream called")):
            response = self.client.post("/dhan/index-ltp-batch")
        self.assertEqual(response.status_code, 403)

    @patch("backend.server.Path.read_text", return_value="test-token")
    @patch("backend.server.DhanFeed")
    def test_three_indexes_one_provider_request(self, feed, _token):
        feed.return_value.batch_ltp.return_value = {"status": "success", "data": {
            "IDX_I": {"13": {"last_price": 25144.3}, "25": {"last_price": 57000.5}},
            "BSE_I": {"51": {"last_price": 82000.25}},
        }}
        response = self.client.post("/dhan/index-ltp-batch", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(set(body["quotes"]), {"NIFTY", "BANKNIFTY", "SENSEX"})
        self.assertEqual(body["unavailable"], [])
        self.assertEqual(body["quotes"]["SENSEX"]["security_id"], "51")
        self.assertEqual(body["freshness"], "unverified")
        self.assertFalse(body["live_orders_enabled"])
        feed.return_value.batch_ltp.assert_called_once_with(
            [("IDX_I", 13), ("IDX_I", 25), ("BSE_I", 51)])

    @patch("backend.server.Path.read_text", return_value="test-token")
    @patch("backend.server.DhanFeed")
    def test_partial_index_response_does_not_fabricate_prices(self, feed, _token):
        feed.return_value.batch_ltp.return_value = {"status": "success", "data": {
            "IDX_I": {"13": {"last_price": 25144.3}, "25": {"last_price": 0}},
        }}
        response = self.client.post("/dhan/index-ltp-batch", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()["quotes"]), {"NIFTY"})
        self.assertEqual(response.json()["unavailable"], ["BANKNIFTY", "SENSEX"])

    @patch("backend.server.Path.read_text", return_value="test-token")
    @patch("backend.server.DhanFeed")
    def test_rate_limit_returns_retry_after(self, feed, _token):
        feed.return_value.batch_ltp.side_effect = DhanRateLimitError("cooldown")
        response = self.client.post("/dhan/index-ltp-batch", headers=self.headers)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers.get("retry-after"), "30")
