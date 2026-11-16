"""Two-second validated Oracle equity snapshot coalescing: offline only."""
import sys
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from server_feed import ServerDhanReadOnly
from refresh_coordinator import LaneCoordinator
from market_feed import FeedError


class EquitySnapshotCoalescingTests(TestCase):
    def setUp(self):
        self.client = ServerDhanReadOnly()
        self.client._origin = "https://example.org"
        self.client._pairing_key = "unit-test-not-real-key"
        self.now = [100.0]
        self.client._lane_coordinator = LaneCoordinator(clock=lambda: self.now[0], max_cached=8)

    def test_two_second_validated_snapshot_is_reused_without_broker_request(self):
        expected = {"RELIANCE": {"symbol": "RELIANCE", "price": 100,
                                 "source": "Dhan", "live_verified": False,
                                 "freshness": "unverified", "snapshot_age_seconds": 30}}
        with patch.object(self.client, "batch_quotes", return_value=expected) as snapshot:
            one = self.client.equity_quotes_with_bootstrap()
            one["RELIANCE"]["price"] = 1
            two = self.client.equity_quotes_with_bootstrap()
            self.assertEqual(two["RELIANCE"]["price"], 100)
            self.assertFalse(two["RELIANCE"]["live_verified"])
            snapshot.assert_called_once_with()
            self.now[0] = 102.0
            self.client.equity_quotes_with_bootstrap()
            self.assertEqual(snapshot.call_count, 2)

    def test_source_math_is_bound_before_age_closure(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "server_feed.py").read_text()
        start = source.index("    def equity_quotes_with_bootstrap(self):")
        end = source.index("    def intraday(self,", start)
        local = source[start:end]
        self.assertLess(local.index("            import math"),
                        local.index("            def still_within_source_age("))
        self.assertIn("math.isfinite(row", local)

    def test_near_120s_snapshot_expires_before_two_second_ttl(self):
        def snap(age, price):
            return {"RELIANCE": {"symbol": "RELIANCE", "price": price,
                                 "snapshot_age_seconds": age,
                                 "source": "Dhan", "freshness": "unverified",
                                 "live_verified": False}}
        with patch.object(self.client, "batch_quotes",
                          side_effect=[snap(119.6, 100), snap(10, 101)]) as fetch:
            self.assertEqual(self.client.equity_quotes_with_bootstrap()["RELIANCE"]["price"], 100)
            self.now[0] = 100.5
            self.assertEqual(self.client.equity_quotes_with_bootstrap()["RELIANCE"]["price"], 101)
            self.assertEqual(fetch.call_count, 2)

    def test_unknown_cached_snapshot_age_never_reused(self):
        rows = {"RELIANCE": {"price": 100}}
        with patch.object(self.client, "batch_quotes", side_effect=[rows, rows]) as fetch:
            self.client.equity_quotes_with_bootstrap()
            self.client.equity_quotes_with_bootstrap()
            self.assertEqual(fetch.call_count, 2)

    def test_malformed_snapshot_does_not_get_cached_or_trigger_broker(self):
        invalid = FeedError("Invalid Oracle Dhan snapshot quote")
        with patch.object(self.client, "batch_quotes", side_effect=[invalid, {"RELIANCE": {"price": 100, "snapshot_age_seconds": 30}}]) as snapshot:
            with patch.object(self.client, "_call", side_effect=AssertionError("must not call Dhan")):
                with self.assertRaises(FeedError):
                    self.client.equity_quotes_with_bootstrap()
                got = self.client.equity_quotes_with_bootstrap()
        self.assertEqual(got["RELIANCE"]["price"], 100)
        self.assertEqual(snapshot.call_count, 2)

    def test_disconnect_and_reconnect_never_reuse_older_session_quotes(self):
        with patch.object(self.client, "batch_quotes", return_value={"RELIANCE": {"price": 100, "snapshot_age_seconds": 30}}):
            self.client.equity_quotes_with_bootstrap()
        self.client.disconnect()
        self.client._origin = "https://example.org"
        self.client._pairing_key = "new-unit-test-only-key"
        with patch.object(self.client, "batch_quotes", return_value={"RELIANCE": {"price": 200, "snapshot_age_seconds": 30}}) as fresh:
            value = self.client.equity_quotes_with_bootstrap()
        self.assertEqual(value["RELIANCE"]["price"], 200)
        fresh.assert_called_once_with()

    def test_legacy_unverified_quote_validation_still_within_batch_quotes(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "server_feed.py").read_text()
        a = source.index("    def batch_quotes(self):")
        b = source.index("    def equity_quotes_with_bootstrap(self):", a)
        section = source[a:b]
        self.assertIn('result.get("collection_status") != "recently_collected"', section)
        self.assertIn("age > 120", section)
        self.assertIn('result.get("live_verified") is True', section)
        self.assertIn('self._call("/v2/snapshot")', section)
        self.assertNotIn("_lane_coordinator.run(", section)


if __name__ == "__main__":
    main()
