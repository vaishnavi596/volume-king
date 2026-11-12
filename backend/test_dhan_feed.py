"""Offline tests for the read-only Dhan quote adapter."""
import io
import json
import unittest
import urllib.error
from dhan_feed import DhanFeed, DhanFeedError, DhanRateLimitError

class Response:
    def __init__(self, data):
        self.data = data
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, limit):
        return json.dumps(self.data).encode()

class DhanFeedTests(unittest.TestCase):
    def test_ltp_payload(self):
        def opener(request, timeout):
            self.assertEqual(timeout, 12)
            self.assertEqual(request.get_method(), "POST")
            self.assertEqual(json.loads(request.data), {"IDX_I": [13]})
            return Response({"status": "success", "data": {"IDX_I": {"13": {"last_price": 25030.35}}}})
        result = DhanFeed("client", "secret", opener=opener).ltp("IDX_I", 13)
        self.assertEqual(result["data"]["IDX_I"]["13"]["last_price"], 25030.35)

    def test_historical_rate_limit_does_not_block_ltp(self):
        previous = (DhanFeed._retry_after, DhanFeed._historical_retry_after,
                    DhanFeed._intraday_next_allowed)
        calls = []
        def opener(request, timeout):
            calls.append(request.full_url)
            if request.full_url.endswith("/charts/intraday"):
                raise urllib.error.HTTPError(request.full_url, 429, "rate limit", {}, None)
            return Response({"status": "success", "data": {"NSE_EQ": {}}})
        try:
            DhanFeed._retry_after = 0
            DhanFeed._historical_retry_after = 0
            DhanFeed._intraday_next_allowed = 0
            feed = DhanFeed("client", "secret", opener=opener)
            with self.assertRaises(DhanRateLimitError):
                feed.intraday({"securityId": "2885"})
            self.assertIn("data", feed.ltp("NSE_EQ", 2885))
            with self.assertRaises(DhanRateLimitError):
                feed.intraday({"securityId": "2885"})
            self.assertEqual(len(calls), 2)
        finally:
            (DhanFeed._retry_after, DhanFeed._historical_retry_after,
             DhanFeed._intraday_next_allowed) = previous

    def test_invalid_security_id(self):
        with self.assertRaises(DhanFeedError):
            DhanFeed("client", "secret").ltp("IDX_I", "invalid")

    def test_auth_failure_has_no_secret(self):
        def opener(request, timeout):
            raise urllib.error.HTTPError(request.full_url, 401, "unauthorized", {}, None)
        with self.assertRaises(DhanFeedError) as caught:
            DhanFeed("client", "very-secret-token", opener=opener).ltp("IDX_I", 13)
        self.assertNotIn("very-secret-token", str(caught.exception))

if __name__ == "__main__":
    unittest.main()
