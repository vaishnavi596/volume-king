"""Source-level preservation guard for original V1 controls in Clone B1/B2."""
import ast
import unittest
from pathlib import Path

MAIN = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
TREE = ast.parse(MAIN)
FUNCS = {n.name for n in ast.walk(TREE)
         if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


class OriginalV1FeaturePreservation(unittest.TestCase):
    def test_original_v1_controls_still_present(self):
        for name in ("settings", "legacy_save_settings", "refresh_option_expiry",
                     "refresh_selected_options", "store_filters", "filter_mode_changed",
                     "trigger_scan", "run_scan", "scan_market", "fill_watch",
                     "refresh_watch_batch", "super_five_card", "dashboard",
                     "central_filter_settings"):
            with self.subTest(name=name):
                self.assertIn(name, FUNCS)

    def test_saved_filter_and_option_preferences_still_present(self):
        for key in ("scanner_filters", "scanner_added_filters", "filter_modes",
                    "scanner_chart_indicators", "scanner_chart_style",
                    "scanner_timeframe", "scanner_period", "scanner_refresh",
                    "option_expiry_choice", "option_expiry", "option_symbol",
                    "watchlist_"):
            with self.subTest(key=key):
                self.assertIn(key, MAIN)

    def test_good_b1_b2_safety_extensions_not_reverted(self):
        for fragment in ("MAX_ACTIVE_FILTERS=len(filter_names)",
                         '["1m","2m","3m","5m","10m","15m","30m","1h"]',
                         'source_interval=("1m" if interval in ("2m","3m")',
                         "completed_two_minute_bars(", "completed_three_minute_bars(",
                         "MAX_WATCHLIST_EQUITIES=70",
                         'if not allow_network and prefs.get("source")=="Dhan":',
                         "no saved completed candles • auto scan WAIT",
                         "broker-listed expiries", 'expiry.value=""',
                         "priority_equity_batch(", "watch_three_minute_signal("):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, MAIN)

    def test_index_dropdown_order_does_not_change_identity_mapping(self):
        # Shared selector used by Options, Scanner and search menus.
        section = MAIN.split("    def selection_symbols():", 1)[1].split(
            "    def sync_symbol_choices():", 1)[0]
        self.assertIn('["NIFTY","BANKNIFTY","SENSEX","FINNIFTY"]', section)
        self.assertIn("dict.fromkeys(", section)
        # The selected underlying is carried by its symbol, never dropdown index.
        self.assertIn('value=prefs.get("option_symbol","NIFTY")', MAIN)
        self.assertIn("dhan_feed.option_expiries,sym", MAIN)

    def test_option_expiry_remains_broker_verified(self):
        section = MAIN.split("    def refresh_option_expiry(", 1)[1].split(
            "    def add_option_symbol(", 1)[0]
        self.assertIn('expiry.value=""', section)
        self.assertIn("refresh_selected_options", section)
        self.assertNotIn("option_dates(chain_symbol.value)", section)

    def test_option_source_caption_matches_verified_entitlements(self):
        self.assertIn("broker-listed option metrics only for verified, entitled underlyings", MAIN)
        self.assertNotIn("and NIFTY option metrics. Option freshness", MAIN)
        self.assertIn('dhan_feed.option_expiries,sym', MAIN)
        self.assertIn('dhan_feed.option_chain_metrics,sym,chosen', MAIN)

    def test_historical_data_not_labeled_live(self):
        self.assertIn('freshness="historical_unverified"', MAIN)
        self.assertIn("live_verified=False", MAIN)


if __name__ == "__main__":
    unittest.main()
