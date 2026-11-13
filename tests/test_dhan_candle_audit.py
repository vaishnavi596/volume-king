"""Offline safety tests for read-only Dhan 51-equity candle audit."""
import datetime as dt
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATH = ROOT / "backend" / "audit-dhan-51-candles.py"
SPEC = importlib.util.spec_from_file_location("audit_dhan_51_candles", PATH)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class CandleAuditSessionTests(unittest.TestCase):
    def setUp(self):
        self.day = dt.date(2026, 11, 12)
        start = dt.datetime(2026, 11, 12, 9, 15, tzinfo=AUDIT.IST).timestamp()
        self.bars = [[start + i * 300, 100, 101, 99, 100, 1000] for i in range(30)]

    def test_valid_trading_session(self):
        self.assertTrue(AUDIT.bars_match_requested_day(self.bars, self.day))

    def test_wrong_day_rejected(self):
        self.assertFalse(AUDIT.bars_match_requested_day(self.bars, self.day - dt.timedelta(days=1)))

    def test_insufficient_candles_rejected(self):
        self.assertFalse(AUDIT.bars_match_requested_day(self.bars[:29], self.day))

    def test_before_open_and_at_close_rejected(self):
        before = [row[:] for row in self.bars]
        before[0][0] -= 300
        self.assertFalse(AUDIT.bars_match_requested_day(before, self.day))
        after = [row[:] for row in self.bars]
        after[-1][0] = dt.datetime(2026, 11, 12, 15, 30, tzinfo=AUDIT.IST).timestamp()
        self.assertFalse(AUDIT.bars_match_requested_day(after, self.day))

    def test_invalid_timestamp_fails_closed(self):
        for timestamp in (float("inf"), 10**30, None):
            invalid = [row[:] for row in self.bars]
            invalid[0][0] = timestamp
            self.assertFalse(AUDIT.bars_match_requested_day(invalid, self.day))


if __name__ == "__main__":
    unittest.main()
