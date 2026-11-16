"""Read-only Oracle readiness shared-cache integration tests, no HTTP/network."""
import sys
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from market_feed import FeedError
from server_feed import ServerDhanReadOnly

VALID = {
    "live_orders_enabled": False,
    "orders": {"broker_submission_allowed": False,
               "live_orders_enabled": False},
    "collector": {"status": "not_collected", "configured_enabled": False},
}


class ReadinessCoalescingTests(TestCase):
    def setUp(self):
        self.feed = ServerDhanReadOnly()
        self.feed._origin = "https://example.org"
        self.feed._pairing_key = "test-only-not-real"

    def test_validated_readiness_is_reused_without_extra_network(self):
        with patch.object(self.feed, "_call", return_value=VALID) as call:
            one = self.feed.server_readiness()
            one["orders"]["live_orders_enabled"] = True
            two = self.feed.server_readiness()
        self.assertEqual(two["orders"]["live_orders_enabled"], False)
        call.assert_called_once_with("/v2/server-readiness")

    def test_unsafe_readiness_never_cached(self):
        invalid = {"live_orders_enabled": True, "orders": VALID["orders"]}
        with patch.object(self.feed, "_call", side_effect=[invalid, VALID]) as call:
            with self.assertRaises(FeedError):
                self.feed.server_readiness()
            self.assertEqual(self.feed.server_readiness()["live_orders_enabled"], False)
        self.assertEqual(call.call_count, 2)

    def test_missing_or_malformed_response_is_not_cached(self):
        with patch.object(self.feed, "_call", side_effect=[None, VALID]) as call:
            with self.assertRaises(FeedError):
                self.feed.server_readiness()
            self.assertEqual(self.feed.server_readiness()["orders"]["broker_submission_allowed"], False)
        self.assertEqual(call.call_count, 2)

    def test_disconnect_prevents_cache_leak_to_another_session(self):
        with patch.object(self.feed, "_call", return_value=VALID) as call:
            self.feed.server_readiness()
        self.feed.disconnect()
        with self.assertRaises(FeedError):
            self.feed.server_readiness()
        self.feed._origin = "https://example.org"
        self.feed._pairing_key = "new-test-only-not-real"
        with patch.object(self.feed, "_call", return_value=VALID) as next_call:
            self.feed.server_readiness()
        next_call.assert_called_once_with("/v2/server-readiness")

    def test_market_data_paths_do_not_use_readiness_cache(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "server_feed.py").read_text(encoding="utf-8")
        a = source.index("    def batch_quotes(self):")
        b = source.index("    def equity_quotes_with_bootstrap(self):", a)
        self.assertIn('self._call("/v2/snapshot")', source[a:b])
        self.assertNotIn("_lane_coordinator.run(", source[a:b])


if __name__ == "__main__":
    main()
