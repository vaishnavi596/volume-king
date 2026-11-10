"""Offline regression tests for the Android Dhan gateway 429 cooldown."""
import io
import os
import sys
import time
import unittest
import urllib.error
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from server_feed import ServerDhanReadOnly
from market_feed import FeedError


class DhanCooldownTests(unittest.TestCase):
    def setUp(self):
        with ServerDhanReadOnly._cooldown_lock:
            ServerDhanReadOnly._cooldown_until = 0.0
        self.feed = ServerDhanReadOnly()
        self.feed._origin = "https://example.org"
        self.feed._pairing_key = "dummy-pairing-key"

    def tearDown(self):
        with ServerDhanReadOnly._cooldown_lock:
            ServerDhanReadOnly._cooldown_until = 0.0

    def test_429_blocks_other_feed_instances_without_network(self):
        calls = []
        def fail_429(req, timeout):
            calls.append(req.full_url)
            raise urllib.error.HTTPError(req.full_url, 429, "limited",
                                         {"Retry-After": "45"}, io.BytesIO(b"secret"))
        with patch("urllib.request.build_opener") as opener:
            opener.return_value.open.side_effect = fail_429
            with self.assertRaisesRegex(FeedError, "HTTP 429"):
                self.feed._call("/dhan/ltp", {"symbol": "NIFTY"})
            second = ServerDhanReadOnly()
            second._origin = self.feed._origin
            second._pairing_key = self.feed._pairing_key
            with self.assertRaisesRegex(FeedError, "retry after"):
                second._call("/dhan/intraday", {"symbol": "RELIANCE"})
        self.assertEqual(len(calls), 1)
        self.assertGreater(ServerDhanReadOnly._cooldown_until, time.monotonic() + 40)

    def test_status_remains_accessible_during_cooldown(self):
        with ServerDhanReadOnly._cooldown_lock:
            ServerDhanReadOnly._cooldown_until = time.monotonic() + 30
        with patch("urllib.request.build_opener") as opener:
            response = opener.return_value.open.return_value.__enter__.return_value
            response.read.return_value = b'{"live_orders_enabled": false, "market_data_configured": true}'
            result = self.feed._call("/dhan/status")
        self.assertTrue(result["market_data_configured"])
        opener.return_value.open.assert_called_once()


if __name__ == "__main__":
    unittest.main()
