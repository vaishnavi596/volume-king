"""Offline Dhan adapter tests: no credentials sent to real providers."""
import io
import json
import unittest
import urllib.error
from unittest.mock import patch
from backend.dhan_feed import DhanFeed, DhanFeedError, DhanRateLimitError


class FakeResponse:
    def __init__(self, data):
        self.data = json.dumps(data).encode()
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, size=-1): return self.data


class DhanFeedTests(unittest.TestCase):
    def setUp(self):
        # Global provider cooldown must not leak across independent offline tests.
        self._previous_retry_after = DhanFeed._retry_after
        DhanFeed._retry_after = 0.0
        self.addCleanup(setattr, DhanFeed, "_retry_after", self._previous_retry_after)

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

    def test_invalid_segments_and_boolean_ids(self):
        feed = DhanFeed("owner", "private-token", opener=lambda *a: self.fail("Network must not be used"))
        with self.assertRaises(DhanFeedError):
            feed.ltp("UNVERIFIED", 13)
        with self.assertRaises(DhanFeedError):
            feed.ltp("IDX_I", True)
        with self.assertRaises(DhanFeedError):
            feed.ltp("IDX_I", 13.9)
        with self.assertRaises(DhanFeedError):
            feed.ltp("IDX_I", "13.9")

    def test_rate_limit_is_safe(self):
        def opener(req, timeout):
            raise urllib.error.HTTPError(req.full_url, 429, "rate limit", {}, io.BytesIO(b"private-token"))
        feed = DhanFeed("owner", "private-token", opener=opener)
        with self.assertRaises(DhanFeedError) as caught:
            feed.ltp("IDX_I", 13)
        self.assertIn("rate limit", str(caught.exception).lower())
        self.assertNotIn("private-token", str(caught.exception))

    def test_rate_limit_cooldown_is_shared_across_instances(self):
        calls = []
        def throttled(req, timeout):
            calls.append(req.full_url)
            raise urllib.error.HTTPError(req.full_url, 429, "rate limit", {}, io.BytesIO(b"secret"))
        first = DhanFeed("owner", "secret", opener=throttled)
        second = DhanFeed("owner", "secret", opener=throttled)
        with patch("backend.dhan_feed.time.monotonic", return_value=100.0):
            with self.assertRaises(DhanRateLimitError):
                first.ltp("IDX_I", 13)
            with self.assertRaisesRegex(DhanRateLimitError, "cooldown"):
                second.ltp("IDX_I", 13)
        self.assertEqual(len(calls), 1, "Cooldown must prevent a second upstream call")
        self.assertGreaterEqual(DhanFeed._retry_after, 130.0)

    def test_rate_limit_cooldown_expires_without_live_network(self):
        calls = []
        def opener(req, timeout):
            calls.append(1)
            return FakeResponse({"status": "success", "data": {}})
        feed = DhanFeed("owner", "secret", opener=opener)
        DhanFeed._retry_after = 130.0
        with patch("backend.dhan_feed.time.monotonic", return_value=129.9):
            with self.assertRaises(DhanRateLimitError):
                feed.ltp("IDX_I", 13)
        with patch("backend.dhan_feed.time.monotonic", return_value=130.0):
            feed.ltp("IDX_I", 13)
        self.assertEqual(len(calls), 1)

    def test_trading_endpoint_cannot_be_called(self):
        feed = DhanFeed("owner", "private-token", opener=lambda *a: self.fail("Network should not be used"))
        with self.assertRaises(DhanFeedError):
            feed._post("/orders", {})


if __name__ == "__main__":
    unittest.main()
