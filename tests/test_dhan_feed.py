"""Offline Dhan adapter tests: no credentials sent to real providers."""
import io
import json
import unittest
import urllib.error
from unittest.mock import Mock
from backend.dhan_feed import DhanFeed, DhanFeedError


class FakeResponse:
    def __init__(self, data):
        self.data = json.dumps(data).encode()
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, size=-1): return self.data


class DhanFeedTests(unittest.TestCase):
    def test_missing_credentials(self):
        with self.assertRaises(DhanFeedError):
            DhanFeed("", "")

    def test_ltp_is_read_only_and_uses_security_id(self):
        requests = []
        def opener(req, timeout):
            requests.append((req, timeout))
            return FakeResponse({"status": "success", "data": {"NSE_EQ": {"1333": {"last_price": 100}}}})
        feed = DhanFeed("owner", "private-token", opener=opener)
        data = feed.ltp("NSE_EQ", 1333)
        self.assertEqual(data["status"], "success")
        req, timeout = requests[0]
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(req.full_url, "https://api.dhan.co/v2/marketfeed/ltp")
        self.assertEqual(json.loads(req.data), {"NSE_EQ": [1333]})
        self.assertEqual(timeout, 12)

    def test_token_is_not_in_error(self):
        def opener(req, timeout):
            raise urllib.error.HTTPError(req.full_url, 401, "secret", {}, io.BytesIO(b"private-token"))
        feed = DhanFeed("owner", "private-token", opener=opener)
        with self.assertRaises(DhanFeedError) as ctx:
            feed.ltp("NSE_EQ", 1333)
        self.assertNotIn("private-token", str(ctx.exception))

    def test_unmapped_symbol_is_rejected(self):
        feed = DhanFeed("owner", "private-token", opener=lambda *a: self.fail("Network should not be used"))
        with self.assertRaises(DhanFeedError):
            feed.ltp("NSE_EQ", "NIFTY")
        with self.assertRaises(DhanFeedError):
            feed.intraday({})

    def test_trading_endpoint_cannot_be_called(self):
        feed = DhanFeed("owner", "private-token", opener=lambda *a: self.fail("Network should not be used"))
        with self.assertRaises(DhanFeedError):
            feed._post("/orders", {})


if __name__ == "__main__":
    unittest.main()
