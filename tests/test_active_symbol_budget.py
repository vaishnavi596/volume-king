"""No-network, pure workload-budget tests for SDC-4."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from active_symbol_budget import plan_active_symbols, plan_due_history_symbols


class Sdc4BudgetTests(unittest.TestCase):
    def test_fifty_one_plus_three_then_remove_twenty(self):
        symbols = [f"STOCK{i:02d}" for i in range(51)]
        before = plan_active_symbols([symbols, [], [], [], []])
        after = plan_active_symbols([symbols[20:], [], [], [], []])
        self.assertEqual((before.watched_equities, before.total_instruments), (51, 54))
        self.assertEqual((after.watched_equities, after.total_instruments), (31, 34))
        self.assertEqual(after.unused_equity_slots, 39)

    def test_removed_watchlist_symbol_stays_if_visible_scanner_or_dashboard(self):
        budget = plan_active_symbols([["RELIANCE"], [], [], [], []],
            scanner=["HDFCBANK"], dashboard=["TCS", "NIFTY"],
            super_five=["INFY"], options=["ICICIBANK"])
        self.assertEqual(budget.watched_equities, 1)
        self.assertEqual(budget.extra_equities, 4)
        self.assertIn("HDFCBANK", budget.equities)
        self.assertEqual(budget.total_instruments, 8)

    def test_duplicate_legacy_prefs_must_be_normalized_first(self):
        with self.assertRaises(ValueError):
            plan_active_symbols([["RELIANCE"], ["RELIANCE"], [], [], []])

    def test_over_seventy_rejected_without_requests(self):
        with self.assertRaises(ValueError):
            plan_active_symbols([[f"STOCK{i:03d}" for i in range(71)], [], [], [], []])

    def test_invalid_or_nonfive_watchlists_fail_closed(self):
        for groups in ([], [[], [], [], []], [["NIFTY"], [], [], [], []],
                       [["bad symbol"], [], [], [], []]):
            with self.subTest(groups=groups), self.assertRaises(ValueError):
                plan_active_symbols(groups)

    def test_due_history_batch_never_fans_out_all_fifty_one(self):
        symbols = [f"STOCK{i:02d}" for i in range(51)]
        plan = plan_active_symbols([symbols, [], [], [], []])
        due = plan_due_history_symbols(plan, now=300, max_batch=3)
        self.assertEqual(len(due), 3)
        self.assertEqual(len(set(due)), 3)
        self.assertTrue(set(due).issubset(set(plan.indices + plan.equities)))

    def test_cooldown_blocks_all_requests(self):
        plan = plan_active_symbols([["RELIANCE"], [], [], [], []])
        self.assertEqual(plan_due_history_symbols(plan, now=300, cooldown_until=330), ())

    def test_recent_and_expired_attempts(self):
        plan = plan_active_symbols([["RELIANCE"], [], [], [], []], keep_indices=())
        self.assertEqual(plan_due_history_symbols(plan, now=250,
            last_attempts={"RELIANCE": 100}, minimum_spacing=180), ())
        self.assertEqual(plan_due_history_symbols(plan, now=280,
            last_attempts={"RELIANCE": 100}, minimum_spacing=180), ("RELIANCE",))

    def test_rejects_unbounded_or_nonfinite_inputs(self):
        plan = plan_active_symbols([["RELIANCE"], [], [], [], []])
        for options in ({"max_batch": 4}, {"max_batch": 0},
                        {"minimum_spacing": 0}, {"now": float("nan")},
                        {"last_attempts": {"RELIANCE": float("inf")}}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                plan_due_history_symbols(plan, **dict({"now":300}, **options))

    def test_mapped_symbols_whitelist_skips_unverified_candles(self):
        plan = plan_active_symbols([["RELIANCE", "TCS"], [], [], [], []])
        due = plan_due_history_symbols(
            plan, now=1000, mapped_symbols={"TCS", "NIFTY"}, max_batch=3)
        self.assertEqual(set(due), {"TCS", "NIFTY"})
        self.assertNotIn("RELIANCE", due)
        self.assertNotIn("SENSEX", due)
        self.assertEqual(plan_due_history_symbols(
            plan, now=1000, mapped_symbols=set()), ())

    def test_invalid_broker_mapping_fails_closed(self):
        plan = plan_active_symbols([["RELIANCE"], [], [], [], []])
        for mapped in ("RELIANCE", {"RELIANCE", "bad symbol"}, [123]):
            with self.subTest(mapped=mapped), self.assertRaises(ValueError):
                plan_due_history_symbols(plan, now=1000, mapped_symbols=mapped)

    def test_global_request_gap_blocks_rapid_repeat_cycles(self):
        budget = plan_active_symbols([["RELIANCE", "TCS"], [], [], [], []])
        self.assertEqual(plan_due_history_symbols(
            budget, now=101, last_global_attempt=100, global_spacing=1.5), ())
        due = plan_due_history_symbols(
            budget, now=101.5, last_global_attempt=100, global_spacing=1.5)
        self.assertGreater(len(due), 0)
        self.assertLessEqual(len(due), 3)

    def test_global_gap_validation_fails_closed(self):
        budget = plan_active_symbols([["RELIANCE"], [], [], [], []])
        for kwargs in (
                {"last_global_attempt": float("nan")},
                {"last_global_attempt": 101},
                {"global_spacing": 0},
                {"global_spacing": float("inf")}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                plan_due_history_symbols(budget, now=100, **kwargs)

    def test_does_not_assume_any_provider_call_count(self):
        budget = plan_active_symbols([["RELIANCE", "TCS"], [], [], [], []])
        self.assertFalse(hasattr(budget, "saved_api_calls"))
        self.assertEqual(budget.indices, ("BANKNIFTY", "NIFTY", "SENSEX"))


if __name__ == "__main__":
    unittest.main()
