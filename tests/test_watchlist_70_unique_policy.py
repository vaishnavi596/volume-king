"""Offline regression for BOT KING 70 distinct NSE equities / five lists."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from watchlist_policy import normalize_watchlists, MAX_EQUITIES


class Watchlist70PolicyTests(unittest.TestCase):
    def test_exactly_70_unique_equities_can_be_saved_across_five_lists(self):
        symbols = [f"EQ{i:03d}" for i in range(70)]
        result = normalize_watchlists([
            symbols[:20], symbols[20:35], symbols[35:50],
            symbols[50:60], symbols[60:],
        ])
        self.assertEqual(sum(len(group) for group in result), 70)
        self.assertEqual([s for g in result for s in g], symbols)
        self.assertEqual(MAX_EQUITIES, 70)

    def test_71st_is_rejected_and_earlier_list_owns_duplicate(self):
        symbols = [f"EQ{i:03d}" for i in range(71)]
        result = normalize_watchlists([
            symbols[:20], ["EQ000", "EQ020"] + symbols[20:40],
            symbols[40:55], symbols[55:65], symbols[65:],
        ])
        flattened = [s for group in result for s in group]
        self.assertEqual(len(flattened), 70)
        self.assertEqual(len(set(flattened)), 70)
        self.assertEqual(result[0][0], "EQ000")
        self.assertNotIn("EQ000", result[1])
        self.assertNotIn("EQ070", flattened)

    def test_legacy_duplicate_hdfc_across_saved_watchlists(self):
        result = normalize_watchlists([
            ["HDFCBANK", "RELIANCE"],
            ["hdfcbank", "TCS"], ["RELIANCE.NS", "INFY"], [], [],
        ])
        self.assertEqual(result, [
            ["HDFCBANK", "RELIANCE"], ["TCS"], ["INFY"], [], [],
        ])

    def test_corrupt_prefs_cannot_create_fake_tickers_or_overcap(self):
        result = normalize_watchlists([
            ["SBIN", None, " ", {"x": 1}, "BANK NIFTY", "ÄBC"],
            "RELIANCE", 5, None, ["SBIN", "ICICIBANK"],
        ])
        self.assertEqual(result, [
            ["SBIN"], [], [], [], ["ICICIBANK"],
        ])

    def test_idempotent_order_and_no_unintended_deletion_for_valid_saved_lists(self):
        groups = [["RELIANCE", "HDFCBANK"], ["TCS"], [], ["INFY"], []]
        self.assertEqual(normalize_watchlists(groups), groups)
        self.assertEqual(normalize_watchlists(normalize_watchlists(groups)), groups)

    def test_app_wires_policy_on_load_and_add_guards(self):
        source = (ROOT / "src/main.py").read_text(encoding="utf-8")
        self.assertIn("normalize_watchlists(saved_watch_groups", source)
        self.assertIn("MAX_TOTAL_INSTRUMENTS=70", source)
        self.assertIn("MAX_WATCHLIST_EQUITIES=MAX_TOTAL_INSTRUMENTS-3", source)
        self.assertIn("normalize_watchlists(saved_watch_groups, maximum=70)", source)
        self.assertIn("def watch_symbol_owner(sym):", source)
        self.assertIn("owner=watch_symbol_owner(sym)", source)
        self.assertIn("len(all_watch_symbols())>=MAX_WATCHLIST_EQUITIES", source)


if __name__ == "__main__":
    unittest.main()
