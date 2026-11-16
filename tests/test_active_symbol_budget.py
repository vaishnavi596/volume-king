"""No-network, pure workload-budget tests for SDC-4."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from active_symbol_budget import plan_active_symbols


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

    def test_does_not_assume_any_provider_call_count(self):
        budget = plan_active_symbols([["RELIANCE", "TCS"], [], [], [], []])
        self.assertFalse(hasattr(budget, "saved_api_calls"))
        self.assertEqual(budget.indices, ("BANKNIFTY", "NIFTY", "SENSEX"))


if __name__ == "__main__":
    unittest.main()
