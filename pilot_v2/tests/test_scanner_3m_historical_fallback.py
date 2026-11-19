"""V2 offline scanner 3m from cached completed 1m bars; never live."""
import unittest
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from candle_history import LocalCandleHistory
from historical_three_minute_fallback import HistoricalThreeMinuteFallback

IST = timezone(timedelta(hours=5, minutes=30))

class ThreeMinuteFallbackTests(unittest.TestCase):
    def setUp(self):
        self.start = int(datetime(2026, 11, 18, 9, 15, tzinfo=IST).timestamp())
        self.history = LocalCandleHistory()
        self.overlay = HistoricalThreeMinuteFallback(
            self.history, clock=lambda: self.start + 360)

    def insert(self, count=6):
        bars = [
            {"timestamp": self.start + i * 60,
             "open": 100., "high": 102., "low": 99.,
             "close": 101., "volume": 5., "completed": True}
            for i in range(count)]
        self.history.accept("TCS", "1m", 1, bars, allowed_symbols=("TCS",))

    def test_two_complete_three_minute_candles_are_historical_only(self):
        self.insert()
        view = self.overlay.view("TCS", "3m", selected_equities=("TCS",))
        self.assertEqual(view["count"], 2)
        self.assertFalse(view["verified_live"])
        self.assertEqual(view["derived_from"], "cached_1m")
        self.assertEqual(view["bars"][0]["volume"], 15)
        self.assertEqual(self.history.view("TCS", "3m",
            selected_equities=("TCS",))["status"], "WAIT")

    def test_missing_minute_or_forming_bar_is_wait(self):
        self.insert(5)
        self.assertEqual(self.overlay.view("TCS", "3m",
                         selected_equities=("TCS",))["status"], "WAIT")
        self.overlay.clock = lambda: self.start + 359
        self.assertEqual(self.overlay.view("TCS", "3m",
                         selected_equities=("TCS",))["status"], "WAIT")

    def test_removed_symbol_and_independent_index(self):
        self.insert()
        self.assertEqual(self.overlay.view("TCS", "3m")["status"], "WAIT")
        self.assertEqual(self.overlay.view("NIFTY", "3m")["status"], "WAIT")
        self.history.accept("TCS", "3m", 1, [
            {"timestamp":self.start+i*180,"open":100.,"high":102.,
             "low":99.,"close":101.,"volume":15.,"completed":True}
            for i in range(2)],allowed_symbols=("TCS",))
        direct = self.overlay.view("TCS", "3m", selected_equities=("TCS",))
        self.assertNotIn("derived_from", direct)
    def test_scanner_uses_overlay_for_historical_chart_only(self):
        source = (SRC / "main.py").read_text(encoding="utf-8")
        self.assertIn("scanner_history = HistoricalThreeMinuteFallback(candle_history)", source)
        self.assertIn("historical_scanner_analysis(\n                    scanner_history", source)
        self.assertIn("return [_native_bar_stack(c) for c in candle_geometry(", source)
        self.assertIn("refresh_visible_native_chart(symbol, timeframe)", source)
        self.assertIn('filter_evidence.rows(scanner[0].symbol', source)

if __name__ == "__main__":
    unittest.main()
