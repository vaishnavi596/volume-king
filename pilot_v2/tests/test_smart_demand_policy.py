"""Shared V2 app demand priorities: pure offline contract tests."""
import unittest
from pilot_v2.smart_demand_policy import plan_demands, PRIORITY


class SmartDemandTests(unittest.TestCase):
    def test_one_reliance_quote_shared_by_watchlist_and_decision(self):
        plan = plan_demands([
            ("watchlist_visible", ("RELIANCE",)),
            ("manual_decision", ("RELIANCE",)),
        ])
        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0].feed, "quotes")
        self.assertEqual(plan[0].priority, PRIORITY["interactive"])
        self.assertEqual(plan[0].freshness_seconds, 30)
        self.assertEqual(set(plan[0].consumers),
                         {"watchlist_visible", "manual_decision"})

    def test_index_independent_of_watchlist(self):
        plan = plan_demands([
            ("index_dashboard", ("NIFTY", "BANKNIFTY", "SENSEX")),
            ("watchlist_visible", ("RELIANCE",)),
        ])
        self.assertEqual(len(plan), 4)
        self.assertEqual({p.feed for p in plan}, {"indices", "quotes"})
        self.assertTrue(all(p.priority == 1 for p in plan if p.feed == "indices"))

    def test_scanner_candle_reused_by_superfive(self):
        plan = plan_demands([
            ("selected_scanner", ("TCS",)),
            ("super_five_visible", ("TCS",)),
            ("historical_backfill", ("TCS",)),
        ])
        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0].feed, "candles")
        self.assertEqual(plan[0].priority, 0)
        self.assertEqual(len(plan[0].consumers), 3)

    def test_background_does_not_override_fast_priority(self):
        plan = plan_demands([
            ("historical_backfill", ("RELIANCE",)),
            ("selected_scanner", ("RELIANCE",)),
        ])
        self.assertEqual(plan[0].freshness_seconds, 30)

    def test_invalid_symbols_and_requests_blocked(self):
        for req in ([("bad", ("TCS",))],
                    [("manual_decision", (["TCS"],))],
                    [("watchlist_visible", ("tcs",))],
                    [("watchlist_visible", tuple("X" + str(i) for i in range(71)))]):
            with self.subTest(req=str(req)[:60]):
                with self.assertRaises(ValueError):
                    plan_demands(req)

    def test_no_order_execution_in_plan(self):
        plan = plan_demands([("manual_decision", ("RELIANCE",))])
        self.assertEqual(plan[0].feed, "quotes")
        self.assertFalse(hasattr(plan[0], "order"))
        self.assertFalse(hasattr(plan[0], "side"))


if __name__ == "__main__":
    unittest.main()
