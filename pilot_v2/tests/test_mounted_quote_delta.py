"""Static gate for actual mounted Flet quote-label delta wiring, no network."""
import ast
import unittest
from pathlib import Path

MAIN = Path(__file__).resolve().parents[1] / "android_app" / "src" / "main.py"


class MountedQuoteDeltaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = MAIN.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source, filename=str(MAIN))

    def test_data_only_callback_never_full_page_renders(self):
        callback = next(n for n in ast.walk(self.tree)
                        if isinstance(n, ast.FunctionDef)
                        and n.name == "apply_data_only_quote_snapshot")
        source = ast.get_source_segment(self.source, callback)
        self.assertIn("quote_view.apply_feed(", source)
        self.assertIn("quote_view.changed_for(", source)
        self.assertIn("control.update()", source)
        self.assertNotIn("render()", source)
        self.assertNotIn("page.update()", source.split("return changed")[0].replace(
            "# No page.update() or render() on data-only change.", ""))
        self.assertNotIn("ft.Column(", source)
        self.assertNotIn("ft.NavigationBar(", source)
        self.assertNotIn("http", source.lower())

    def test_visible_labels_registered_on_dashboard_scanner_watchlist(self):
        text = self.source
        self.assertIn('tracked_quote_text(card["symbol"], card["price_label"], "index"', text)
        self.assertIn('tracked_quote_text(symbol, quote_view.display(symbol, state.selected)', text)
        self.assertIn('tracked_quote_text(scanner[0].symbol, quote_view.display(', text)
        self.assertIn('tracked_quote_text(row["symbol"], row["symbol"] + "  " + row["price"], "watchlist"', text)
        self.assertIn("quote_labels.clear()", text)
        self.assertIn("watchlist_row(", text)
        self.assertIn('if control.value != new_value:', text)

    def test_candle_delta_uses_trusted_source_gate_and_mounted_labels_only(self):
        callback = next(n for n in ast.walk(self.tree)
                        if isinstance(n, ast.FunctionDef)
                        and n.name == "apply_data_only_candle_snapshot")
        fragment = ast.get_source_segment(self.source, callback)
        self.assertIn("evidence_inbox.apply_candles(", fragment)
        self.assertIn("trusted_transport=trusted_transport", fragment)
        self.assertIn("if not accepted:", fragment)
        self.assertIn("control.update()", fragment)
        self.assertNotIn("render()", fragment)
        self.assertNotIn("page.update()", fragment)
        self.assertIn('tracked_candle_text(card["symbol"], "1m"', self.source)
        self.assertIn('tracked_candle_text(symbol, "1m", candle_history.summary(', self.source)
        self.assertIn('tracked_candle_text(scanner[0].symbol, scanner[0].timeframe,', self.source)
        self.assertIn('tracked_candle_text(row["symbol"], "3m", row["candle"], "watchlist"', self.source)
        self.assertIn("candle_labels.clear()", self.source)

    def test_filter_update_reads_existing_evidence_and_never_ingests_signals(self):
        callback = next(n for n in ast.walk(self.tree)
                        if isinstance(n, ast.FunctionDef)
                        and n.name == "refresh_visible_filter_labels")
        fragment = ast.get_source_segment(self.source, callback)
        self.assertIn("shared_filter_context(", fragment)
        self.assertIn("control.update()", fragment)
        for forbidden in ("render()", "page.update()", "accept_available(",
                          "apply_option_factors(", "trusted_transport=True",
                          "requests.", "httpx."):
            self.assertNotIn(forbidden, fragment)
        self.assertIn('tracked_filter_text(row["symbol"], "3m", row["filter_text"]', self.source)
        self.assertIn('tracked_filter_text(card["symbol"], "1m"', self.source)
        self.assertIn("filter_labels.clear()", self.source)
        self.assertIn('context["rows"]', fragment)

    def test_filter_evidence_wrappers_require_original_trust_gates(self):
        for method, guarded in (
            ("apply_data_only_candle_trend_evidence", "evidence_inbox.apply_candle_trend("),
            ("apply_data_only_option_factor_evidence", "evidence_inbox.apply_option_factors("),
        ):
            with self.subTest(method=method):
                callback = next(n for n in ast.walk(self.tree)
                                if isinstance(n, ast.FunctionDef) and n.name == method)
                fragment = ast.get_source_segment(self.source, callback)
                self.assertIn(guarded, fragment)
                self.assertIn("trusted_transport=trusted_transport", fragment)
                self.assertIn("selected_equities=state.selected", fragment)
                self.assertIn("if accepted:", fragment)
                self.assertIn("refresh_visible_filter_labels(symbol, timeframe)", fragment)
                for forbidden in ("render()", "page.update()", "trusted_transport=True",
                                  "requests.", "httpx.", "submit_order("):
                    self.assertNotIn(forbidden, fragment)

    def test_native_chart_repaints_without_full_page_or_new_market_fetch(self):
        callback = next(n for n in ast.walk(self.tree)
                        if isinstance(n, ast.FunctionDef)
                        and n.name == "apply_data_only_candle_snapshot")
        fragment = ast.get_source_segment(self.source, callback)
        self.assertIn("evidence_inbox.apply_candles(", fragment)
        self.assertIn("if not accepted:", fragment)
        self.assertIn("refresh_visible_native_chart(symbol, timeframe)", fragment)
        self.assertNotIn("page.update()", fragment)
        self.assertNotIn("render()", fragment)
        helper = next(n for n in ast.walk(self.tree)
                      if isinstance(n, ast.FunctionDef)
                      and n.name == "refresh_visible_native_chart")
        helper_source = ast.get_source_segment(self.source, helper)
        self.assertIn("control.content = new_content", helper_source)
        self.assertIn("control.controls = new_content", helper_source)
        self.assertIn("control.update()", helper_source)
        self.assertNotIn("page.update()", helper_source)
        self.assertIn("native_chart_hosts.clear()", self.source)
        self.assertIn('tracked_native_chart(scanner[0].symbol, scanner[0].timeframe, "line")', self.source)
        self.assertIn('tracked_native_chart(scanner[0].symbol, scanner[0].timeframe, "candles")', self.source)
        self.assertIn("ft.LineChart(", self.source)
        self.assertIn("candle_geometry(", self.source)

    def test_technical_panel_follows_only_accepted_cached_candles(self):
        callback = next(n for n in ast.walk(self.tree)
                        if isinstance(n, ast.FunctionDef)
                        and n.name == "apply_data_only_candle_snapshot")
        text = ast.get_source_segment(self.source, callback)
        self.assertIn("refresh_visible_technical(symbol, timeframe)", text)
        self.assertIn("if not accepted:", text)
        helper = next(n for n in ast.walk(self.tree)
                      if isinstance(n, ast.FunctionDef)
                      and n.name == "refresh_visible_technical")
        src = ast.get_source_segment(self.source, helper)
        self.assertIn("historical_scanner_analysis(", src)
        self.assertIn("historical_indicator_panel(", src)
        self.assertIn("control.controls = ", src)
        for unwanted in ("render()", "page.update()", "accept_available(",
                         "trusted_transport=True", "requests.", "httpx."):
            self.assertNotIn(unwanted, src)
        self.assertIn("technical_hosts.clear()", self.source)
        self.assertIn("tracked_technical_summary(", self.source)
        self.assertIn("tracked_indicator_panel(", self.source)

    def test_no_unverified_feed_pretends_to_be_live_transport(self):
        self.assertNotIn("submit_order(", self.source)
        self.assertNotIn("ServerAngelFeed(", self.source)
        self.assertNotIn("get_yahoo(", self.source)


if __name__ == "__main__":
    unittest.main()
