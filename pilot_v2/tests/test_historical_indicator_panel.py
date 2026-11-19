"""V1→V2 read-only technical panel parity: shared verified history only."""
import ast
import sys
import unittest
from pathlib import Path
SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from evidence_inbox import DeviceEvidenceInbox
from historical_indicator_panel import historical_indicator_panel
from test_ft2_historical_chart_context import bars

class HistoricalIndicatorPanelTests(unittest.TestCase):
    def test_without_candles_wait_and_roster_isolated(self):
        cache = DeviceEvidenceInbox()
        before = historical_indicator_panel(
            cache.candles, "TCS", "3m", selected_equities=("TCS",))
        self.assertEqual(len(before), 1)
        self.assertIn("WAIT", before[0])
        cache.apply_candles("TCS", "3m", 1, bars(n=36),
                            selected_equities=("TCS",), trusted_transport=True)
        self.assertEqual(historical_indicator_panel(
            cache.candles, "TCS", "3m"), before)
        panel = historical_indicator_panel(
            cache.candles, "TCS", "3m", selected_equities=("TCS",))
        self.assertEqual(len(panel), 3)
        self.assertIn("EMA20", panel[0])
        self.assertIn("EMA50", panel[0])
        self.assertIn("RSI14", panel[1])
        self.assertIn("ATR14", panel[1])
        self.assertIn("support", panel[2])
        self.assertIn("unverified", panel[2])

    def test_partial_refresh_does_not_destroy_panel(self):
        cache = DeviceEvidenceInbox()
        cache.apply_candles("TCS", "3m", 1, bars(n=36),
                            selected_equities=("TCS",), trusted_transport=True)
        before = historical_indicator_panel(
            cache.candles, "TCS", "3m", selected_equities=("TCS",))
        with self.assertRaises(ValueError):
            cache.apply_candles(
                "TCS", "3m", 2,
                bars(n=36)[:-1] + [dict(bars(n=36)[-1], completed=False)],
                selected_equities=("TCS",), trusted_transport=True)
        self.assertEqual(historical_indicator_panel(
            cache.candles, "TCS", "3m", selected_equities=("TCS",)), before)

    def test_ui_same_cache_and_independent_five_filters(self):
        source = (SRC / "main.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("from historical_indicator_panel import historical_indicator_panel", source)
        self.assertIn("historical_indicator_panel(", source)
        self.assertIn("scanner_history, scanner[0].symbol, scanner[0].timeframe", source)
        self.assertIn("Sixth filter: reserved / blank", source)
        self.assertNotIn("ServerAngelFeed(", source)

if __name__ == "__main__":
    unittest.main()
