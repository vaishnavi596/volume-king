"""Official 2026 NSE/BSE equity session-gating test; no network/quotes/orders."""
import pathlib
import sys
import unittest
from datetime import datetime, timedelta, timezone

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from v3_equity_session_calendar import (
    IST,EQUITY_HOLIDAYS_2026,ist_clock,regular_equity_day,
    regular_equity_hours,equity_refresh_window
)

def dt(y,m,d,h=11,minute=0,tz=IST):
    return datetime(y,m,d,h,minute,tzinfo=tz)

class V3EquityHolidayCalendar(unittest.TestCase):
    def test_exchange_2026_holiday_list_and_today_holiday(self):
        self.assertEqual(len(EQUITY_HOLIDAYS_2026),16)
        for stamp in EQUITY_HOLIDAYS_2026:
            with self.subTest(day=stamp):
                date=datetime.fromisoformat(stamp).date()
                day=dt(date.year,date.month,date.day)
                self.assertFalse(regular_equity_day(day))
                self.assertFalse(regular_equity_hours(day))
                self.assertFalse(equity_refresh_window(day))
        self.assertFalse(regular_equity_hours(dt(2026,11,24,12,0)))
        self.assertFalse(equity_refresh_window(dt(2026,11,24,9,30)))

    def test_normal_weekday_and_ist_boundary_times(self):
        # Wed Nov 25 is a regular trading day following holiday Tue Nov 24.
        day=lambda hour,minute:dt(2026,11,25,hour,minute)
        self.assertTrue(regular_equity_day(day(12,0)))
        self.assertFalse(regular_equity_hours(day(9,14)))
        self.assertTrue(regular_equity_hours(day(9,15)))
        self.assertTrue(regular_equity_hours(day(15,29)))
        self.assertFalse(regular_equity_hours(day(15,30)))
        self.assertFalse(equity_refresh_window(day(9,9)))
        self.assertTrue(equity_refresh_window(day(9,10)))
        self.assertTrue(equity_refresh_window(day(15,44)))
        self.assertFalse(equity_refresh_window(day(15,45)))

    def test_weekend_special_not_inferred_as_ordinary_session(self):
        self.assertFalse(regular_equity_hours(dt(2026,11,8,14,20)))
        self.assertFalse(equity_refresh_window(dt(2026,11,8,14,20)))
        self.assertFalse(regular_equity_hours(dt(2026,11,28,12,0)))

    def test_timezone_normalization_and_naive_rejection(self):
        utc=timezone.utc
        self.assertFalse(regular_equity_hours(dt(2026,11,24,6,0,utc)))
        self.assertTrue(regular_equity_hours(dt(2026,11,25,6,0,utc)))
        self.assertEqual(ist_clock(dt(2026,11,25,6,0,utc)).hour,11)
        with self.assertRaises(ValueError):
            regular_equity_hours(datetime(2026,11,25,11,0))

    def test_unverified_2027_future_year_cannot_claim_live_or_refresh(self):
        # An official 2027 NSE/BSE equity calendar has not been confirmed.
        # Weekday alone cannot authorize LIVE analysis or automatic Dhan polls.
        for value in (dt(2027,1,4,9,15),dt(2027,1,4,11,30),
                      dt(2027,12,31,14,0),dt(2028,1,3,12,0)):
            with self.subTest(day=value.date().isoformat()):
                self.assertFalse(regular_equity_day(value))
                self.assertFalse(regular_equity_hours(value))
                self.assertFalse(equity_refresh_window(value))
        self.assertTrue(regular_equity_hours(dt(2026,12,31,11,30)))

    def test_phone_market_and_refresh_production_contract(self):
        source=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
        section=source.split("    def regular_hours(now=None):",1)[1].split(
            "    def session_caption():",1)[0]
        self.assertIn("return regular_equity_hours(now)",section)
        self.assertIn("return equity_refresh_window(now)",section)
        self.assertIn("    from v3_equity_session_calendar import regular_equity_hours, equity_refresh_window",source)

if __name__=="__main__":
    unittest.main()
