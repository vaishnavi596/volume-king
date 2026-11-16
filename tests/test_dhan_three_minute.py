"""Network-free 1m -> 3m historical candle quality regressions."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dhan_three_minute import completed_three_minute_bars

IST = timezone(timedelta(hours=5, minutes=30))


def epoch(day=16, hour=9, minute=15):
    return int(datetime(2026, 11, day, hour, minute, tzinfo=IST).timestamp())


class CompletedThreeMinuteBarsTest(unittest.TestCase):
    def test_three_full_minutes_are_one_candle(self):
        t = epoch()
        bars = [(t, 100, 104, 99, 102, 5),
                (t+60, 102, 106, 101, 105, 7),
                (t+120, 105, 107, 103, 106, 11)]
        self.assertEqual(completed_three_minute_bars(bars, now_epoch=t+180),
                         [(t, 100, 107, 99, 106, 23)])

    def test_partially_formed_group_is_excluded(self):
        t = epoch()
        bars = [(t, 100, 101, 99, 100, 1),
                (t+60, 100, 102, 99, 101, 1),
                (t+120, 101, 103, 100, 102, 1)]
        self.assertEqual(completed_three_minute_bars(bars, now_epoch=t+150), [])
        self.assertEqual(len(completed_three_minute_bars(bars, now_epoch=t+180)), 1)

    def test_missing_middle_minute_is_not_synthetic(self):
        t = epoch()
        self.assertEqual(completed_three_minute_bars([
            (t, 100, 102, 99, 101, 1),
            (t+120, 101, 103, 100, 102, 1),
        ], now_epoch=t+300), [])

    def test_session_anchor_does_not_use_midnight_utc(self):
        t = epoch()
        bars = [(t+180+i*60, 100, 101, 99, 100, 1) for i in range(3)]
        self.assertEqual(completed_three_minute_bars(bars, now_epoch=t+360),
                         [(t+180, 100, 101, 99, 100, 3)])

    def test_invalid_ohlc_and_duplicate_dont_fabricate(self):
        t = epoch()
        self.assertEqual(completed_three_minute_bars([
            (t, 100, 99, 101, 100, 1),
            (t+60, 100, 102, 99, 101, 1),
            (t+120, 101, 103, 100, 102, 1),
        ], now_epoch=t+180), [])
        self.assertEqual(completed_three_minute_bars("bad", now_epoch=t+180), [])
        self.assertEqual(completed_three_minute_bars([], now_epoch=float("nan")), [])

    def test_duplicate_minute_rejects_entire_bucket(self):
        t = epoch()
        bars = [
            (t, 100, 101, 99, 100, 1),
            (t+60, 100, 103, 99, 101, 2),
            (t+60, 100, 107, 98, 106, 20),
            (t+120, 101, 104, 100, 102, 3),
        ]
        # A duplicate provider record must not produce a misleading green
        # or red Watchlist 3-minute vote or double-counted volume.
        self.assertEqual(completed_three_minute_bars(bars, now_epoch=t+180), [])

    def test_scanner_real_dhan_3m_path_is_supported_without_yahoo(self):
        # Structural check: existing Dhan gateway must fetch one-minute source,
        # not invent an unsupported native Dhan 3-minute endpoint.
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
        self.assertIn('source_interval="1m" if interval=="3m" else interval', source)
        self.assertIn('bars=completed_three_minute_bars(candle_result["bars"],now_epoch=time.time())', source)
        self.assertIn('scanner_intervals=(["1m","3m","5m","15m","1h"]', source)
        self.assertNotIn('{"1m":1,"3m":3,"5m":5', source)

    def test_3m_scanner_does_not_overwrite_shared_5m_signal_contract(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
        self.assertIn('report_identity=(sym,"5m",identity)', source)
        self.assertIn('watch_signal_cache[sym]=dict(result,symbol=sym)', source)
        self.assertIn('hist=await asyncio.wait_for(asyncio.to_thread(get_market_data,sym,interval,period),timeout=45)', source)

    def test_different_trading_days_never_merge(self):
        t1, t2 = epoch(16), epoch(17)
        self.assertEqual(completed_three_minute_bars([
            (t1, 100, 101, 99, 100, 1),
            (t1+60, 100, 101, 99, 100, 1),
            (t2+120, 100, 101, 99, 100, 1),
        ], now_epoch=t2+180), [])


if __name__ == "__main__":
    unittest.main()
