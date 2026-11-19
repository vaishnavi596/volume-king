"""One shared provider quota, priority/cooldown isolation, no broker calls."""
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from pilot_v2.internal_dhan_read_port import DhanReadBatch, InternalDhanReadPort, DhanRateLimited
from pilot_v2.shared_read_budget import SharedReadBudget, BudgetDenied
from pilot_v2.unified_data_pipeline import V2UnifiedReadPipeline, PipelineUnavailable


class SharedBudgetTests(unittest.TestCase):
    def setUp(self):
        self.t = 100.0
        self.calls = []
        self.budget = SharedReadBudget(
            monotonic=lambda: self.t, min_gap_seconds=1, cooldown_seconds=30)

        def transport(feed, symbols):
            self.calls.append((feed, symbols))
            return DhanReadBatch(
                "dhan", symbols,
                {s: {"price": 100, "observed_at": 1800000000} for s in symbols},
                len(self.calls), 1800000000)

        port = InternalDhanReadPort(
            transport=transport, selected_equities=("RELIANCE",),
            clock=lambda: 1800000000)
        self.pipeline = V2UnifiedReadPipeline(
            read_port=port,
            clock=lambda: datetime(2026, 11, 19, 10, 0,
                                   tzinfo=ZoneInfo("Asia/Kolkata")),
            monotonic=lambda: self.t, read_budget=self.budget)

    def test_shared_cache_prevents_duplicate_calls(self):
        self.pipeline.dispatch("verified-device-001", "quotes")
        self.pipeline.dispatch("verified-device-002", "quotes")
        self.assertEqual(len(self.calls), 1)

    def test_manual_bypasses_cache_but_not_quota(self):
        self.pipeline.dispatch("verified-device-001", "quotes")
        with self.assertRaises(PipelineUnavailable):
            self.pipeline.dispatch("verified-device-001", "quotes", manual=True)
        self.assertEqual(len(self.calls), 1)
        self.t += 1.1
        self.pipeline.dispatch("verified-device-001", "quotes", manual=True)
        self.assertEqual(len(self.calls), 2)

    def test_indices_share_global_budget_with_equities(self):
        self.pipeline.dispatch("verified-device-001", "quotes")
        with self.assertRaises(PipelineUnavailable):
            self.pipeline.dispatch("verified-device-001", "indices")
        self.t += 1
        self.pipeline.dispatch("verified-device-001", "indices")
        self.assertEqual(len(self.calls), 2)

    def test_429_cooldown_blocks_all_lanes_and_manual(self):
        self.budget.throttle()
        for feed in ("quotes", "indices"):
            with self.assertRaises(PipelineUnavailable):
                self.pipeline.dispatch("verified-device-001", feed, manual=True)
        self.assertEqual(self.calls, [])
        self.t += 30
        self.pipeline.dispatch("verified-device-001", "indices")
        self.assertEqual(len(self.calls), 1)

    def test_actual_transport_rate_limit_sets_shared_cooldown(self):
        def refused(*_):
            raise DhanRateLimited("HTTP 429")
        self.pipeline._port._transport = refused
        with self.assertRaises(PipelineUnavailable):
            self.pipeline.dispatch("verified-device-001", "quotes")
        self.assertEqual(self.budget.status()["cooldown_seconds"], 30)
        self.assertEqual(self.calls, [])

        # Subsequent requests for either lane cannot contact transport.
        self.pipeline._port._transport = lambda *_: self.fail(
            "Transport must not be invoked under cooldown")
        with self.assertRaises(PipelineUnavailable):
            self.pipeline.dispatch("verified-device-001", "indices", manual=True)
        self.t += 30.1
        self.assertEqual(self.budget.status()["cooldown_seconds"], 0)

    def test_generic_transport_error_does_not_fake_a_429(self):
        def unavailable(*_):
            raise OSError("Offline")
        self.pipeline._port._transport = unavailable
        with self.assertRaises(PipelineUnavailable):
            self.pipeline.dispatch("verified-device-001", "quotes")
        self.assertEqual(self.budget.status()["cooldown_seconds"], 0)

    def test_invalid_quota_clock_and_config_fail_closed(self):
        with self.assertRaises(ValueError):
            SharedReadBudget(monotonic=lambda: 1, min_gap_seconds=0)
        self.t = float("nan")
        with self.assertRaises(BudgetDenied):
            self.budget.reserve()

    def test_unsupported_lanes_never_consume_budget(self):
        for feed in ("candles", "options", "assessment", "scanner"):
            with self.assertRaises(PipelineUnavailable):
                self.pipeline.dispatch("verified-device-001", feed)
        self.assertEqual(self.budget.status()["next_read_seconds"], 0.0)


if __name__ == "__main__":
    unittest.main()
