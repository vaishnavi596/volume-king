"""V1 read-only control audit, V2 native chart parity segment.

This is a *source evidence* audit. Do not treat a string presence or an offline
test as Android UI/WebView acceptance. No legacy provider imports executed.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
LEGACY = ROOT / "src" / "main.py"
V2 = ROOT / "pilot_v2" / "android_app" / "src" / "main.py"


class V1V2NativeControlParity(unittest.TestCase):
    def test_known_v1_chart_controls_and_v2_safe_native_equivalent(self):
        v1 = LEGACY.read_text(encoding="utf-8")
        v2 = V2.read_text(encoding="utf-8")
        ast.parse(v2)
        for original in (
            "def scanner_chart_style_change(e):",
            "def scanner_compact_chart():",
            "def scanner_chart_toggle(e):",
            "def refresh_selected_options",
            "def sync_visible_chart",
        ):
            with self.subTest(control=original):
                self.assertIn(original, v1)
        for safe in (
            'label="Scanner chart style"',
            "on_change=change_chart_style",
            'chart_style[0] == "Candles"',
            'chart_style[0] == "Line"',
            "candle_geometry(",
            "chart_points(",
            "on_change=select_scanner_timeframe",
            "on_change=change_chart_window",
            "on_change=select_expiry",
            "on_click=select_historical_candidate",
        ):
            with self.subTest(control=safe):
                # Super Five local candidate clicks use a closure: check
                # their callback separately instead of relying on V1 source.
                if safe == "on_click=select_historical_candidate":
                    self.assertIn("select_historical_candidate(symbol)", v2)
                else:
                    self.assertIn(safe, v2)
        self.assertNotIn("ft.WebView(", v2)
        self.assertNotIn("ServerAngelFeed(", v2)

    def test_v1_richer_webview_is_still_an_unverified_android_gap(self):
        v1 = LEGACY.read_text(encoding="utf-8")
        v2 = V2.read_text(encoding="utf-8")
        self.assertIn("ft.WebView(", v1)
        self.assertNotIn("ft.WebView(", v2)
        self.assertIn('ft.NavigationDestination(', v2)
        self.assertEqual(v2.count("ft.NavigationDestination("), 3)

if __name__ == "__main__":
    unittest.main()
