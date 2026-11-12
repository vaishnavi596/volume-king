"""Regression guards for the Oracle-owned Dhan snapshot adapter."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from server_feed import ServerDhanReadOnly, FeedError


class OracleSnapshotAdapterTests(unittest.TestCase):
    def setUp(self):
        self.feed = ServerDhanReadOnly()
        self.feed._origin = "https://example.com"
        self.feed._pairing_key = "test-only"

    def snapshot(self, **changes):
        data = {"protocol": 2, "source": "dhan", "live_orders_enabled": False,
                "quotes": {"RELIANCE": 1333.7}, "unavailable": [],
                "age_seconds": 7.8, "freshness": "unverified",
                "collection_status": "recently_collected", "error": None}
        data.update(changes)
        return data

    def test_uses_cached_get_not_upstream_batch_post(self):
        with patch.object(self.feed, "_call", return_value=self.snapshot()) as request:
            rows = self.feed.batch_quotes()
        request.assert_called_once_with("/v2/snapshot")
        self.assertEqual(rows["RELIANCE"]["price"], 1333.7)
        self.assertIsNone(rows["RELIANCE"]["quote_timestamp"])
        self.assertEqual(rows["RELIANCE"]["freshness"], "unverified")

    def test_snapshot_cooldown_respects_global_and_route_backoff(self):
        import time
        now=time.monotonic()
        self.feed._global_cooldown_until=now+25
        self.assertGreaterEqual(self.feed.cooldown_remaining("/v2/snapshot"), 24)
        self.feed._global_cooldown_until=0
        self.feed._cooldown_until["/v2/snapshot"]=now+12
        self.assertGreaterEqual(self.feed.cooldown_remaining("/v2/snapshot"), 11)

    def test_accepts_snapshot_within_default_90_second_collection_cycle(self):
        # Dhan upstream collection defaults to 90 seconds, not 30 seconds.
        with patch.object(self.feed, "_call", return_value=self.snapshot(age_seconds=95)):
            self.assertEqual(self.feed.batch_quotes()["RELIANCE"]["price"], 1333.7)

    def test_rejects_old_or_failed_snapshot(self):
        for changes in ({"age_seconds": 121}, {"age_seconds": None},
                        {"live_orders_enabled": True},
                        {"live_orders_enabled": None},
                        {"protocol": 1}, {"source": "yahoo"},
                        {"collection_status": "collection_overdue"},
                        {"collection_status": "awaiting_next_collection"},
                        {"freshness": "stale_or_missing"},
                        {"error": "upstream_http_429"}, {"quotes": {}},
                        {"quotes": {"RELIANCE": 0}},
                        {"unavailable": ["RELIANCE"]}):
            with self.subTest(changes=changes):
                with patch.object(self.feed, "_call", return_value=self.snapshot(**changes)):
                    with self.assertRaises(FeedError):
                        self.feed.batch_quotes()


if __name__ == "__main__":
    unittest.main()
