"""Offline Oracle 226 transport regression tests; no network access."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from oracle_226_client import Oracle226Client, OracleCacheError


class Response:
    status = 200

    def __init__(self, data):
        self.data = json.dumps(data).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size):
        return self.data


class Oracle226Tests(unittest.TestCase):
    def setUp(self):
        self.client = Oracle226Client("https://example.org", "test-only-placeholder")

    def test_device_session_uses_bearer_without_pairing_header(self):
        client = Oracle226Client("https://example.org", "t" * 48,
                                 auth_mode="device_session")
        payload = {"protocol": 2, "quotes": {}, "freshness": "unverified",
                   "live_orders_enabled": False}
        with patch.object(client._opener, "open", return_value=Response(payload)) as opened:
            client.snapshot()
        headers = opened.call_args.args[0].headers
        self.assertEqual(headers.get("Authorization"), "Bearer " + "t" * 48)
        self.assertNotIn("X-botking-key", headers)
        self.assertNotIn("X-BotKing-Key", headers)

    def test_device_session_rejects_malformed_token(self):
        for token in ("t" * 40 + " ", "t" * 40 + ".", "short"):
            with self.subTest(token=repr(token[-1])):
                with self.assertRaises(OracleCacheError):
                    Oracle226Client("https://example.org", token,
                                    auth_mode="device_session")

    def test_snapshot_preserves_unverified_freshness(self):
        payload = {"protocol": 2, "quotes": {"RELIANCE": {"price": 100}},
                   "freshness": "unverified", "live_orders_enabled": False}
        with patch.object(self.client._opener, "open", return_value=Response(payload)):
            self.assertEqual(self.client.snapshot()["freshness"], "unverified")

    def test_candles_remain_historical(self):
        payload = {"symbol": "HDFCBANK", "bars": [[1, 100, 102, 99, 101, 10]],
                   "freshness": "historical_unverified", "live_orders_enabled": False}
        with patch.object(self.client._opener, "open", return_value=Response(payload)):
            self.assertEqual(self.client.candles("HDFCBANK")["freshness"], "historical_unverified")

    def test_unknown_freshness_rejected(self):
        payload = {"protocol": 2, "quotes": {}, "freshness": "verified_live",
                   "live_orders_enabled": False}
        with patch.object(self.client._opener, "open", return_value=Response(payload)):
            with self.assertRaises(OracleCacheError):
                self.client.snapshot()

    def test_live_orders_flag_must_be_false(self):
        payload = {"protocol": 2, "quotes": {}, "freshness": "unverified",
                   "live_orders_enabled": True}
        with patch.object(self.client._opener, "open", return_value=Response(payload)):
            with self.assertRaises(OracleCacheError):
                self.client.snapshot()

    def test_reject_invalid_symbol_before_request(self):
        with self.assertRaises(OracleCacheError):
            self.client.candles("../secret")

    def test_reject_invalid_candle(self):
        payload = {"symbol": "NIFTY", "bars": [[1, 100, float("nan"), 99, 101, 10]],
                   "freshness": "historical_unverified", "live_orders_enabled": False}
        with patch.object(self.client._opener, "open", return_value=Response(payload)):
            with self.assertRaises(OracleCacheError):
                self.client.candles("NIFTY")


if __name__ == "__main__":
    unittest.main()
