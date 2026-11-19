"""Source-level V1→V2 native chart control parity and safe preferences."""
import ast
import sys
import unittest
from pathlib import Path
SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from chart_style import CHART_STYLES, DEFAULT_CHART_STYLE, chart_style_choice

class V2NativeChartStyleTests(unittest.TestCase):
    def test_only_supported_local_styles(self):
        self.assertEqual(CHART_STYLES, ("Candles", "Line"))
        self.assertEqual(DEFAULT_CHART_STYLE, "Candles")
        for style in CHART_STYLES:
            self.assertEqual(chart_style_choice(style), style)
        for bad in (None, True, 1, "", "WebView", "TradingView", "line", " Line "):
            with self.subTest(style=bad), self.assertRaises(ValueError):
                chart_style_choice(bad)

    def test_wiring_source_preserves_both_cache_only_views(self):
        s = (SRC / "main.py").read_text(encoding="utf-8")
        ast.parse(s)
        for name in ("from chart_style import CHART_STYLES, DEFAULT_CHART_STYLE, chart_style_choice",
                     'chart_style_key = "botking.v2.chart_style.v1"',
                     "def change_chart_style(e):",
                     "chart_style[0] = chart_style_choice(e.control.value)",
                     'label="Scanner chart style"',
                     "on_change=change_chart_style",
                     'chart_style[0] == "Line"',
                     'chart_style[0] == "Candles"',
                     "candle_geometry(",
                     "chart_points(",
                     "on_change=change_chart_window"):
            self.assertIn(name, s)
        self.assertEqual(s.count("ft.NavigationDestination("), 3)
        for forbidden in ("ServerAngelFeed(", "get_yahoo(", "submit_order("):
            self.assertNotIn(forbidden, s)

if __name__ == "__main__":
    unittest.main()
