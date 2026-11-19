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

    def test_no_unverified_feed_pretends_to_be_live_transport(self):
        self.assertNotIn("submit_order(", self.source)
        self.assertNotIn("ServerAngelFeed(", self.source)
        self.assertNotIn("get_yahoo(", self.source)


if __name__ == "__main__":
    unittest.main()
