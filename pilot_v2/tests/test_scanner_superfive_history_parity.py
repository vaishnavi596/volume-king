"""Scanner and Super Five use the same cached historical 3m view."""
import sys
import unittest
from pathlib import Path
from datetime import datetime, timedelta, timezone

SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from candle_history import LocalCandleHistory
from historical_three_minute_fallback import HistoricalThreeMinuteFallback
from historical_chart_context import historical_shortlist, choose_historical_shortlist_symbol

IST = timezone(timedelta(hours=5, minutes=30))

class SharedHistoricalViewTests(unittest.TestCase):
    def test_source_wires_same_overlay_to_scanner_and_shortlist(self):
        source = (SRC / "main.py").read_text(encoding="utf-8")
        self.assertIn("choose_historical_shortlist_symbol(\n                        scanner_history,", source)
        self.assertEqual(source.count('historical_shortlist(\n                    scanner_history, state.selected, timeframe="3m")'), 2)
        self.assertIn("historical_scanner_analysis(\n                    scanner_history,", source)

    def test_same_overlay_cannot_publish_live_evidence(self):
        start = int(datetime(2026, 11, 18, 9, 15, tzinfo=IST).timestamp())
        # Complete 1m history includes enough 3m candles for technical analysis.
        one_minute = [{
            "timestamp": start + i * 60,
            "open": 100. + i * .1, "high": 101. + i * .1,
            "low": 99. + i * .1, "close": 100.5 + i * .1,
            "volume": 10., "completed": True
        } for i in range(105)]
        store = LocalCandleHistory()
        store.accept("TCS", "1m", 1, one_minute, allowed_symbols=("TCS",))
        overlay = HistoricalThreeMinuteFallback(
            store, clock=lambda: start + 105 * 60)
        data = overlay.view("TCS", "3m", selected_equities=("TCS",))
        self.assertEqual(data["status"], "HIST")
        self.assertEqual(data["count"], 35)
        self.assertIs(data["verified_live"], False)
        candidates = historical_shortlist(overlay, ("TCS",), timeframe="3m")
        self.assertLessEqual(len(candidates), 1)
        if candidates:
            self.assertEqual(choose_historical_shortlist_symbol(
                overlay, ("TCS",), candidates[0]["symbol"]), "TCS")
            self.assertIn("HIST", candidates[0]["label"])
        self.assertEqual(historical_shortlist(overlay, (), timeframe="3m"), ())

if __name__ == "__main__":
    unittest.main()
