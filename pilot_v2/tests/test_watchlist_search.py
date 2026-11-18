"""V2 Watchlist local search migration; data-only, no server work."""
import ast
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(ROOT))
from watchlist_search import filtered_watchlist_symbols


class LocalWatchlistSearchTests(unittest.TestCase):
    def test_local_case_insensitive_search_keeps_order_and_original_roster(self):
        group = ["RELIANCE", "TCS", "HDFCBANK", "ICICIBANK"]
        original = list(group)
        self.assertEqual(filtered_watchlist_symbols(group, "bank"), ["HDFCBANK", "ICICIBANK"])
        self.assertEqual(filtered_watchlist_symbols(group, "  TcS "), ["TCS"])
        self.assertEqual(filtered_watchlist_symbols(group, ""), group)
        self.assertEqual(filtered_watchlist_symbols(group, "missing"), [])
        self.assertEqual(group, original)

    def test_reject_bad_search_and_duplicate_or_index_group(self):
        with self.assertRaises(ValueError):
            filtered_watchlist_symbols(["TCS", "TCS"], "T")
        with self.assertRaises(ValueError):
            filtered_watchlist_symbols(["NIFTY"], "N")
        with self.assertRaises(ValueError):
            filtered_watchlist_symbols(["TCS"], "x"*65)
        with self.assertRaises(ValueError):
            filtered_watchlist_symbols(["TCS"], None)

    def test_v2_app_ui_search_is_submit_only_and_offline(self):
        source = (ROOT / "main.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("from watchlist_search import filtered_watchlist_symbols", source)
        self.assertIn("def apply_search(e):", source)
        self.assertIn("on_submit=apply_search", source)
        self.assertIn("filtered_watchlist_symbols(state.groups[group[0]], watch_search[0])", source)
        self.assertEqual(source.count("ft.NavigationDestination("), 3)
        self.assertNotIn("ServerAngelFeed(", source)
        self.assertNotIn("get_yahoo(", source)


if __name__ == "__main__":
    unittest.main()
