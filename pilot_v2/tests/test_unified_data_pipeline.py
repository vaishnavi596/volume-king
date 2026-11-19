"""Unified V2 single-pipeline offline tests; no real broker or phone."""
from datetime import datetime
from zoneinfo import ZoneInfo
import unittest

from pilot_v2.internal_dhan_read_port import DhanReadBatch, InternalDhanReadPort
from pilot_v2.unified_data_pipeline import (
    PipelineUnavailable, V2UnifiedReadPipeline, market_poll_allowed,
)

IST = ZoneInfo("Asia/Kolkata")
STOCKS = ("RELIANCE",)
INDEXES = ("NIFTY", "BANKNIFTY", "SENSEX")
TIMESTAMP = 1800000000


class UnifiedPipelineTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.now = 0

        def provider(feed, symbols):
            self.calls.append((feed, symbols))
            return DhanReadBatch(
                source="dhan", symbols=symbols,
                rows={s: {"price": 100.0, "observed_at": TIMESTAMP}
                      for s in symbols},
                revision=len(self.calls), observed_at=TIMESTAMP,
            )

        port = InternalDhanReadPort(
            transport=provider, selected_equities=STOCKS,
            clock=lambda: TIMESTAMP)
        self.local = datetime(2026, 11, 19, 10, 0, tzinfo=IST)
        self.pipeline = V2UnifiedReadPipeline(
            read_port=port, clock=lambda: self.local,
            monotonic=lambda: self.now)

    def test_one_shared_quote_fetch_across_devices(self):
        first = self.pipeline.dispatch("authorized-device-a", "quotes")
        second = self.pipeline.dispatch("authorized-device-b", "quotes")
        self.assertEqual(first, second)
        self.assertEqual(self.calls, [("quotes", STOCKS)])
        self.assertFalse(first["quotes"]["RELIANCE"]["live_verified"])

    def test_indices_have_independent_lane(self):
        self.pipeline.dispatch("authorized-device-a", "quotes")
        self.pipeline.dispatch("authorized-device-a", "indices")
        self.assertEqual(self.calls, [("quotes", STOCKS), ("indices", INDEXES)])

    def test_manual_refresh_bypasses_cache(self):
        self.pipeline.dispatch("authorized-device-a", "quotes")
        self.pipeline.dispatch("authorized-device-a", "quotes", manual=True)
        self.assertEqual(len(self.calls), 2)

    def test_outside_market_hours_auto_blocked_manual_allowed(self):
        self.local = datetime(2026, 11, 19, 17, 1, tzinfo=IST)
        with self.assertRaises(PipelineUnavailable):
            self.pipeline.dispatch("authorized-device-a", "indices")
        self.assertEqual(self.calls, [])
        self.pipeline.dispatch("authorized-device-a", "indices", manual=True)
        self.assertEqual(len(self.calls), 1)

    def test_weekend_gate(self):
        self.assertFalse(market_poll_allowed(datetime(
            2026, 11, 21, 10, 0, tzinfo=IST)))
        self.assertTrue(market_poll_allowed(datetime(
            2026, 11, 19, 9, 10, tzinfo=IST)))

    def test_unconnected_feature_never_calls_provider(self):
        for feature in ("candles", "scanner", "super_five", "options", "assessment"):
            with self.assertRaises(PipelineUnavailable):
                self.pipeline.dispatch("authorized-device-a", feature)
        self.assertEqual(self.calls, [])

    def test_invalid_unverified_identity_rejected(self):
        with self.assertRaises(PipelineUnavailable):
            self.pipeline.dispatch("", "quotes")
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
