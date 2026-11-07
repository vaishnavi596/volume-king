"""Read-only Dhan endpoint contract tests, with mocked token and upstream."""
import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.server import create_app

PAIRING_KEY = "test-only-pairing-key-32-characters-long"

class StubAngel:
    connected = False
    instruments = None
    resolved = {}
    def disconnect(self): pass

class FakeDhan:
    def __init__(self, client, token): pass
    def ltp(self, segment, sid):
        return {"status": "success", "data": {"IDX_I": {"13": {"last_price": 25030.35}}}}
    def intraday(self, payload):
        return {"open": [100, 102], "high": [104, 105], "low": [99, 101],
                "close": [102, 103], "volume": [50, 60],
                "timestamp": [1760000000, 1760000300]}

class DhanEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app(pairing_key=PAIRING_KEY, feed=StubAngel()))
        self.headers = {"X-BotKing-Key": PAIRING_KEY}
        self.env = patch.dict(os.environ, {"DHAN_CLIENT_ID": "test-client"})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_pairing_required(self):
        self.assertEqual(self.client.post("/dhan/ltp", json={"symbol": "NIFTY"}).status_code, 403)
        self.assertEqual(self.client.post("/dhan/intraday", json={
            "symbol": "NIFTY", "interval": 5, "from_date": "2026-01-01",
            "to_date": "2026-01-02"}).status_code, 403)

    def test_unknown_symbol_rejected(self):
        response = self.client.post("/dhan/ltp", json={"symbol": "UNKNOWN"}, headers=self.headers)
        self.assertEqual(response.status_code, 422)

    @patch("backend.server.Path.read_text", return_value="test-token")
    @patch("backend.server.DhanFeed", FakeDhan)
    def test_ltp(self, read_text):
        response = self.client.post("/dhan/ltp", json={"symbol": "NIFTY"}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["ltp"], 25030.35)
        self.assertEqual(response.json()["freshness"], "unverified")
        self.assertFalse(response.json()["live_orders_enabled"])

    @patch("backend.server.Path.read_text", return_value="test-token")
    @patch("backend.server.DhanFeed", FakeDhan)
    def test_candles(self, read_text):
        response = self.client.post("/dhan/intraday", json={
            "symbol": "NIFTY", "interval": 5, "from_date": "2026-01-01",
            "to_date": "2026-01-02"}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["bars"]), 2)
        self.assertEqual(response.json()["freshness"], "historical_unverified")

    @patch("backend.server.Path.read_text", return_value="test-token")
    @patch("backend.server.DhanFeed")
    def test_malformed_candles_rejected(self, feed_class, read_text):
        feed_class.return_value.intraday.return_value = {
            "open": [100], "high": [99], "low": [98],
            "close": [101], "volume": [50], "timestamp": [1760000000]}
        response = self.client.post("/dhan/intraday", json={
            "symbol": "NIFTY", "interval": 5, "from_date": "2026-01-01",
            "to_date": "2026-01-02"}, headers=self.headers)
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("test-token", response.text)

    @patch("backend.server.Path.read_text", side_effect=PermissionError)
    def test_unreadable_token_is_service_unavailable(self, read_text):
        response = self.client.post("/dhan/ltp", json={"symbol": "NIFTY"}, headers=self.headers)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("test-token", response.text)

    def test_invalid_date_range(self):
        response = self.client.post("/dhan/intraday", json={
            "symbol": "NIFTY", "interval": 5, "from_date": "2026-01-01",
            "to_date": "2026-02-01"}, headers=self.headers)
        self.assertEqual(response.status_code, 422)

if __name__ == "__main__":
    unittest.main()
