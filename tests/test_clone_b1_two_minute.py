"""Offline Batch-1 scanner 2m contract: completed Dhan 1m bars only."""
import ast
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dhan_two_minute import completed_two_minute_bars

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

    def test_scanner_routes_2m_via_1m_and_separate_timeframe_cache(self):
        source=Path(__file__).resolve().parents[1].joinpath("src/main.py").read_text()
        ast.parse(source)
        self.assertIn('"2m","3m","5m"', source)
        self.assertIn('source_interval="1m" if interval in ("2m","3m")', source)
        self.assertIn('completed_two_minute_bars(candle_result["bars"]', source)
        self.assertIn('ticker,interval,range_', source)


if __name__ == "__main__":
    unittest.main()
