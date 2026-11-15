"""Offline test: Dhan option 422 backoff isolates contract selections."""
import io
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from server_feed import ServerDhanReadOnly
from market_feed import FeedError

class Reject422:
    def __init__(self):
        self.calls = []
    def open(self, request, timeout=None):
        self.calls.append(request)
        raise urllib.error.HTTPError(request.full_url, 422, "invalid", {}, io.BytesIO(b"{}"))

class OptionNegativeCacheTests(unittest.TestCase):
    def setUp(self):
        self.feed = ServerDhanReadOnly()
        self.feed._origin = "https://example.test"
        self.feed._pairing_key = "synthetic-key"
        self.reject = Reject422()
        p = patch("server_feed.direct_https_opener", return_value=self.reject)
        p.start()
        self.addCleanup(p.stop)

    def test_selection_isolation(self):
        selected = {"symbol":"NIFTY","expiry":"2026-11-17"}
        with self.assertRaisesRegex(FeedError, "option chain.*HTTP 422"):
            self.feed._call("/dhan/option-chain", selected)
        with self.assertRaisesRegex(FeedError, "same contract retry"):
            self.feed._call("/dhan/option-chain", selected)
        self.assertEqual(len(self.reject.calls), 1)
        for payload in ({"symbol":"BANKNIFTY","expiry":"2026-11-17"},
                        {"symbol":"NIFTY","expiry":"2026-11-23"}):
            with self.assertRaises(FeedError):
                self.feed._call("/dhan/option-chain", payload)
        self.assertEqual(len(self.reject.calls), 3)

    def test_expiry_list_separate(self):
        with self.assertRaisesRegex(FeedError, "expiry list.*HTTP 422"):
            self.feed._call("/dhan/option-expiries", {"symbol":"ICICIBANK"})
        with self.assertRaisesRegex(FeedError, "same contract retry"):
            self.feed._call("/dhan/option-expiries", {"symbol":"ICICIBANK"})
        self.assertEqual(len(self.reject.calls), 1)
        with self.assertRaises(FeedError):
            self.feed._call("/dhan/option-expiries", {"symbol":"RELIANCE"})
        self.assertEqual(len(self.reject.calls), 2)

    def test_disconnect_clears(self):
        payload = {"symbol":"NIFTY","expiry":"2026-11-17"}
        with self.assertRaises(FeedError):
            self.feed._call("/dhan/option-chain", payload)
        self.feed.disconnect()
        self.feed._origin, self.feed._pairing_key = "https://example.test", "synthetic-key"
        with self.assertRaises(FeedError):
            self.feed._call("/dhan/option-chain", payload)
        self.assertEqual(len(self.reject.calls), 2)

    def test_cache_bounded(self):
        for i in range(140):
            with self.assertRaises(FeedError):
                self.feed._call("/dhan/option-expiries", {"symbol":f"FAKE{i}"})
        self.assertLessEqual(len(self.feed._invalid_option_until), 128)

if __name__ == "__main__":
    unittest.main()
