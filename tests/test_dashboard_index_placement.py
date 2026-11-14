"""Batch 4: fixed market index cards belong to Dashboard, not equity Watchlist."""
import pathlib
import unittest

SOURCE = (pathlib.Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")

class IndexPlacementTest(unittest.TestCase):
    def test_index_cards_are_dashboard_first(self):
        dashboard = SOURCE.split("    def dashboard():", 1)[1].split("    search=ft.TextField(", 1)[0]
        self.assertIn("dashboard_market_indices(),", dashboard)
        self.assertLess(dashboard.index("dashboard_market_indices(),"), dashboard.index("dashboard_index_analysis(),"))
        self.assertNotIn("data_overview(),", dashboard)
        builder = SOURCE.split("    def dashboard_market_indices():", 1)[1].split("    def dashboard():", 1)[0]
        self.assertIn('index_symbols=("NIFTY", "BANKNIFTY", "SENSEX")', builder)
        self.assertIn("historical_vote_agreement(index_history)", builder)
        self.assertIn("return ft.Column(index_cards", builder)

    def test_watchlist_no_longer_renders_fixed_indices(self):
        watch = SOURCE.split("    def watchlist():", 1)[1].split("    symbol=ft.Dropdown(", 1)[0]
        self.assertNotIn("index_cards", watch)
        self.assertNotIn("index_symbols=", watch)
        self.assertIn("watch_list]", watch)

if __name__ == "__main__":
    unittest.main()
