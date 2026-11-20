"""B3 Patch-1 source regression: responsive watchlist, filter tap and safe chart."""
import ast
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py")
TEXT = SOURCE.read_text(encoding="utf-8")


def section(start, end):
    return TEXT.split(start, 1)[1].split(end, 1)[0]


class PatchOneGuards(unittest.TestCase):
    def test_main_source_parses(self):
        ast.parse(TEXT)

    def test_watchlist_filtered_rows_rebuild_only_on_membership_change(self):
        body = section("    async def watch_visible_tick():", "    def watchlist():")
        self.assertIn("membership!=last_filtered_membership[0]", body)
        self.assertIn("last_filtered_membership[0]=membership", body)
        self.assertIn("tick_signals[sym]", body)

    def test_filter_tap_does_not_directly_rebuild_page(self):
        body = section("    def remove_added_filter(name):", "    filter_query=ft.TextField(")
        self.assertEqual(body.count("request_view_refresh(current[0])"), 2)
        self.assertNotIn("select(current[0])", body)

    def test_unregistered_android_webview_is_not_instantiated(self):
        self.assertIn("embedded_lightweight_supported=False", TEXT)
        self.assertIn('chart_provider[0]=="TradingView Lightweight" and embedded_lightweight_supported', TEXT)
        self.assertIn("Open TradingView in browser", TEXT)
        self.assertIn("native Dhan candles shown instead", TEXT)

    def test_auto_off_status_is_consistent_for_dhan(self):
        body = section("    def refresh_scan_age():", "    async def scan_age_clock():")
        self.assertIn("elif not scan_live.value:", body)
        self.assertNotIn('not scan_live.value and prefs.get("source")!="Dhan"', body)


if __name__ == "__main__":
    unittest.main()
