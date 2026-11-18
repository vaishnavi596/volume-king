"""Safe local historical Scanner window choice and real Flet wiring."""
import ast
import sys
import unittest
from pathlib import Path
SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from chart_window import WINDOWS, DEFAULT_WINDOW, choose_chart_window, window_from_dropdown
from historical_chart_context import chart_points
from evidence_inbox import DeviceEvidenceInbox
from test_ft2_historical_chart_context import bars

class ChartWindowTests(unittest.TestCase):
    def test_strict_choices(self):
        self.assertEqual((WINDOWS, DEFAULT_WINDOW), ((15, 35, 70), 35))
        for n in WINDOWS:
            self.assertEqual(choose_chart_window(n), n)
            self.assertEqual(window_from_dropdown(str(n)), n)
        for n in (14, 16, 200, True, None, "35", 35.0):
            with self.assertRaises(ValueError):
                choose_chart_window(n)
        for n in ("14", "35.0", " 35 ", None, 35):
            with self.assertRaises(ValueError):
                window_from_dropdown(n)

    def test_last_good_history_unchanged_by_view_window(self):
        e = DeviceEvidenceInbox()
        self.assertEqual(chart_points(e.candles, "TCS", "3m",
                         selected_equities=("TCS",), limit=15), ())
        e.apply_candles("TCS", "3m", 1, bars(n=85),
                        selected_equities=("TCS",), trusted_transport=True)
        for n in WINDOWS:
            self.assertEqual(len(chart_points(e.candles, "TCS", "3m",
                             selected_equities=("TCS",), limit=n)), n)
        before = chart_points(e.candles, "TCS", "3m",
                              selected_equities=("TCS",), limit=70)
        with self.assertRaises(ValueError):
            e.apply_candles("TCS", "3m", 2, bars(n=85)[:-1] +
                            [dict(bars(n=85)[-1], completed=False)],
                            selected_equities=("TCS",), trusted_transport=True)
        self.assertEqual(chart_points(e.candles, "TCS", "3m",
                         selected_equities=("TCS",), limit=70), before)

    def test_source_wires_dropdown_without_legacy_calls(self):
        s = (SRC / "main.py").read_text()
        ast.parse(s)
        for needle in ('from chart_window import DEFAULT_WINDOW, WINDOWS, window_from_dropdown',
                       'chart_window = [DEFAULT_WINDOW]', 'def change_chart_window(e):',
                       'chart_window[0] = window_from_dropdown(e.control.value)',
                       'label="Chart history bars"', 'on_change=change_chart_window',
                       'limit=chart_window[0]'):
            self.assertIn(needle, s)
        self.assertEqual(s.count("ft.NavigationDestination("), 3)
        self.assertNotIn("ServerAngelFeed(", s)
        self.assertNotIn("get_yahoo(", s)

if __name__ == "__main__":
    unittest.main()
