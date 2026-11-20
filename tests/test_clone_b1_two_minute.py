"""Offline Batch-1 scanner 2m contract: completed Dhan 1m bars only."""
import ast
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dhan_two_minute import completed_two_minute_bars
from scanner_engine import analyze

IST = timezone(timedelta(hours=5, minutes=30))
START = int(datetime(2026, 11, 20, 9, 15, tzinfo=IST).timestamp())


def minute(n, *, volume=10):
    return [START + 60 * n, 100 + n, 103 + n, 99 + n, 102 + n, volume]


class TwoMinuteContract(unittest.TestCase):
    def test_completed_two_minutes_price_and_volume(self):
        result = completed_two_minute_bars([minute(0), minute(1), minute(2), minute(3)],
                                           now_epoch=START + 240)
        self.assertEqual(result, [
            (START, 100., 104., 99., 103., 20.),
            (START + 120, 102., 106., 101., 105., 20.)
        ])

    def test_incomplete_and_duplicate_minutes_never_publish(self):
        self.assertEqual(completed_two_minute_bars([minute(0)], now_epoch=START+240), [])
        self.assertEqual(completed_two_minute_bars([minute(0), minute(1)],
                                                   now_epoch=START+119), [])
        self.assertEqual(completed_two_minute_bars([minute(0), minute(1), minute(1)],
                                                   now_epoch=START+180), [])

    def test_invalid_rows_and_cross_session_blocked(self):
        invalid = minute(0)
        invalid[2] = 90
        self.assertEqual(completed_two_minute_bars([invalid, minute(1)],
                                                   now_epoch=START+240), [])
        self.assertEqual(completed_two_minute_bars([minute(374), minute(375)],
                                                   now_epoch=START+380*60), [])

    def test_completed_two_minute_series_reaches_scanner_analysis(self):
        candles = [minute(i) for i in range(80)]
        derived = completed_two_minute_bars(candles, now_epoch=START + 80*60)
        self.assertEqual(len(derived), 40)
        result = analyze(derived, selected=["EMA 9/21", "RSI 14", "MACD", "Supertrend"], timeframe="2m")
        self.assertEqual(result["timeframe"], "2m")
        self.assertEqual(result["count"], 40)
        self.assertNotEqual(result["reason"], "Unsupported candle timeframe")
        self.assertEqual(result["timestamp"], derived[-1][0])

    def test_two_minute_spacing_gap_fails_closed(self):
        derived = completed_two_minute_bars([minute(i) for i in range(80)], now_epoch=START + 80*60)
        gap = derived[:15] + derived[16:]
        result = analyze(gap, selected=["EMA 9/21"], timeframe="2m")
        self.assertEqual(result["bias"], "WAIT")
        self.assertEqual(result["reason"], "Irregular candle spacing within trading session")

    def test_scanner_routes_2m_via_1m_and_separate_timeframe_cache(self):
        source=Path(__file__).resolve().parents[1].joinpath("src/main.py").read_text()
        ast.parse(source)
        self.assertIn('"2m","3m","5m"', source)
        self.assertIn('source_interval="1m" if interval in ("2m","3m")', source)
        self.assertIn('completed_two_minute_bars(candle_result["bars"]', source)
        self.assertIn('ticker,interval,range_', source)
        self.assertIn('"2m":(120,187.5,', source)
        self.assertIn('if tf not in ("1m","2m","3m","5m","15m","1h"):', source)
        self.assertIn('if scan_tf.value in ("1m","2m","3m"):', source)
        self.assertIn('if prefs.get("source")=="Dhan" and interval in ("1m","2m","3m"):', source)
        self.assertIn('scan_period.value=period', source)
        self.assertIn('prefs["scanner_period"]=period', source)
        self.assertIn('period="7d"', source)
        self.assertIn('for v in scanner_intervals', source)


if __name__ == "__main__":
    unittest.main()
