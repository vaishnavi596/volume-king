"""Offline-only Day-2 Smart Apply Queue contract tests. No broker or phone calls."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from clone_day2_apply_queue import SmartApplyQueue, Update


class SmartApplyQueueTests(unittest.TestCase):
    def sample(self, section="watchlist", symbol="RELIANCE", revision=1,
               kind="quote", timeframe="", expiry="", value=100):
        return Update(section, symbol, kind, revision, value, timeframe, expiry)

    def test_initial_bootstrap_priority_and_budget(self):
        q = SmartApplyQueue()
        for section in ("chart", "options", "scanner", "watchlist", "dashboard", "super_five"):
            self.assertTrue(q.receive(self.sample(section=section)))
        self.assertEqual([x.section for x in q.apply_tick(2).applied],
                         ["dashboard", "watchlist"])
        self.assertEqual(q.health()["pending"], 4)
        self.assertEqual([x.section for x in q.apply_tick(4).applied],
                         ["scanner", "super_five", "options", "chart"])
        self.assertEqual(q.health()["pending"], 0)

    def test_coalesce_latest_price_preserves_other_symbol(self):
        q = SmartApplyQueue()
        self.assertTrue(q.receive(self.sample(revision=1, value=100)))
        self.assertTrue(q.receive(self.sample(revision=2, value=105)))
        self.assertTrue(q.receive(self.sample(symbol="TCS", revision=1, value=200)))
        self.assertEqual(q.health()["pending"], 2)
        self.assertEqual(q.apply_tick(1).applied[0].value, 105)
        self.assertEqual(q.health()["counts"]["superseded"], 1)

    def test_ignore_stale_out_of_order(self):
        q = SmartApplyQueue()
        q.receive(self.sample(revision=4))
        self.assertFalse(q.receive(self.sample(revision=3)))
        q.apply_tick(1)
        self.assertFalse(q.receive(self.sample(revision=4)))
        self.assertEqual(q.health()["counts"]["stale_ignored"], 2)

    def test_candles_keep_timeframe_and_expiry_isolated(self):
        q = SmartApplyQueue()
        for timeframe, expiry in (("1m", ""), ("3m", ""), ("5m", ""), ("5m", "2026-11-26")):
            self.assertTrue(q.receive(self.sample(kind="candle", timeframe=timeframe, expiry=expiry)))
        self.assertEqual(q.health()["pending"], 4)

    def test_queue_backpressure_reports_health(self):
        q = SmartApplyQueue(max_pending=1)
        q.receive(self.sample())
        self.assertFalse(q.receive(self.sample(symbol="TCS")))
        self.assertEqual(q.health()["state"], "DEGRADED")
        self.assertEqual(q.health()["issues"][-1]["code"], "QUEUE_CAPACITY")
        self.assertEqual(q.health()["pending"], 1)

    def test_apply_failure_keeps_data_for_retry(self):
        q = SmartApplyQueue()
        q.receive(self.sample())
        def bad_apply(_):
            raise RuntimeError("simulated render failure")
        report = q.apply_tick(1, bad_apply)
        self.assertEqual(report.errors[0]["code"], "APPLY_FAILED")
        self.assertEqual(q.health()["pending"], 1)
        self.assertEqual(len(q.apply_tick(1).applied), 1)

    def test_fake_70_stocks_do_not_exceed_tick_budget(self):
        q = SmartApplyQueue()
        for i in range(70):
            q.receive(self.sample(symbol=f"EQ{i:02d}"))
        applied = []
        for _ in range(10):
            applied.extend(q.apply_tick(7).applied)
        self.assertEqual(len(applied), 70)
        self.assertEqual(q.health()["pending"], 0)

    def test_priority_fifo_inside_same_section(self):
        q = SmartApplyQueue()
        for sym in ("AAA", "BBB", "CCC"):
            self.assertTrue(q.receive(self.sample(symbol=sym)))
        self.assertEqual([u.symbol for u in q.apply_tick(3).applied],
                         ["AAA", "BBB", "CCC"])

    def test_diagnostics_are_bounded(self):
        q = SmartApplyQueue(max_pending=1)
        q.receive(self.sample())
        for i in range(180):
            self.assertFalse(q.receive(self.sample(symbol=f"OTHER{i}")))
        self.assertLessEqual(len(q.diagnostics), 100)
        self.assertEqual(q.health()["pending"], 1)

    def test_boolean_revision_is_invalid(self):
        q = SmartApplyQueue()
        self.assertFalse(q.receive(self.sample(revision=True)))
        self.assertEqual(q.health()["issues"][-1]["code"], "INVALID_UPDATE")

    def test_zero_budget_does_not_apply(self):
        q = SmartApplyQueue()
        q.receive(self.sample())
        self.assertEqual(q.apply_tick(0).deferred, 1)

    def test_invalid_candle_is_diagnosed(self):
        q = SmartApplyQueue()
        self.assertFalse(q.receive(self.sample(kind="candle")))
        self.assertEqual(q.health()["issues"][-1]["code"], "INVALID_TIMEFRAME")


if __name__ == "__main__":
    unittest.main()
