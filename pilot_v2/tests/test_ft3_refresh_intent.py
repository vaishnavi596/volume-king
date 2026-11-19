"""FT3 offline app demand refresh policy; absolutely no broker side effects."""
from datetime import datetime
from pathlib import Path
import sys
import unittest
from zoneinfo import ZoneInfo

src = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(src))
from app_state import LocalWatchlists  # noqa: E402
from smart_data import SmartDataSettings, SmartDataError  # noqa: E402
from refresh_intent import make_refresh_intent, LocalRefreshCadence  # noqa: E402

IST=ZoneInfo("Asia/Kolkata")

def selected(n):
    store=LocalWatchlists()
    for i in range(n):
        store.add(i%5,f"EQ{i:03d}")
    return store

def clock(hour,minute):
    return datetime(2026,11,18,hour,minute,tzinfo=IST)

class SmartDataRefreshIntentTests(unittest.TestCase):
    def test_exact_selected_not_full_catalog_and_index_independence(self):
        for n in (0,5,51,70):
            with self.subTest(n=n):
                intent=make_refresh_intent(selected(n),SmartDataSettings(),
                          clock(10,30),confirmed_session=True)
                self.assertTrue(intent.permitted)
                self.assertEqual(len(intent.equities),n)
                self.assertEqual(intent.indexes,("NIFTY","BANKNIFTY","SENSEX"))
                self.assertEqual(intent.equity_seconds,180)
                self.assertEqual(intent.index_signal_timeframe,"1m")
                self.assertEqual(intent.watchlist_candle_timeframe,"3m")

    def test_after_hours_auto_denied_manual_data_only_allowed(self):
        watchlists=selected(5)
        for when in (clock(9,9),clock(15,46)):
            blocked=make_refresh_intent(watchlists,SmartDataSettings(),when,
                                        confirmed_session=True)
            self.assertFalse(blocked.permitted)
            self.assertEqual(blocked.equities,())
            self.assertEqual(blocked.indexes,())
        after=make_refresh_intent(watchlists,SmartDataSettings(),clock(16,0),
                                  confirmed_session=False,manual=True)
        self.assertTrue(after.permitted)
        self.assertEqual(len(after.equities),5)
        self.assertEqual(after.reason,"MANUAL_DATA_REQUEST_ONLY")

    def test_independent_auto_lane_cadence_and_no_duplicate_claims(self):
        cadence = LocalRefreshCadence(index_seconds=60)
        w = selected(5)
        settings = SmartDataSettings(True, 180)
        self.assertEqual(tuple(feed for feed, _ in cadence.claim_auto(
            w, settings, clock(10, 30), monotonic_seconds=1000,
            confirmed_session=True)), ("indices", "quotes"))
        self.assertEqual(cadence.claim_auto(
            w, settings, clock(10, 30), monotonic_seconds=1000,
            confirmed_session=True), ())
        self.assertEqual(cadence.claim_auto(
            w, settings, clock(10, 31), monotonic_seconds=1059,
            confirmed_session=True), ())
        self.assertEqual(tuple(feed for feed, _ in cadence.claim_auto(
            w, settings, clock(10, 31), monotonic_seconds=1060,
            confirmed_session=True)), ("indices",))
        self.assertEqual(tuple(feed for feed, _ in cadence.claim_auto(
            w, settings, clock(10, 33), monotonic_seconds=1180,
            confirmed_session=True)), ("indices", "quotes"))
        self.assertEqual(cadence.claim_auto(
            w, settings, clock(10, 33), monotonic_seconds=1100,
            confirmed_session=True), ())

    def test_auto_cadence_requires_confirmed_open_market_and_selected_equities(self):
        for n in (0, 5, 70):
            with self.subTest(n=n):
                cadence = LocalRefreshCadence()
                w = selected(n)
                self.assertEqual(cadence.claim_auto(
                    w, SmartDataSettings(), clock(10, 30),
                    monotonic_seconds=1000, confirmed_session=False), ())
                lanes = cadence.claim_auto(
                    w, SmartDataSettings(), clock(10, 30),
                    monotonic_seconds=1000, confirmed_session=True)
                self.assertEqual(lanes[0][0], "indices")
                self.assertEqual(len(lanes[0][1]), 3)
                self.assertEqual(len(lanes), 1 if n == 0 else 2)
                if n:
                    self.assertEqual(len(lanes[1][1]), n)
                self.assertEqual(cadence.claim_auto(
                    w, SmartDataSettings(), clock(15, 46),
                    monotonic_seconds=2000, confirmed_session=True), ())
        with self.assertRaises(SmartDataError):
            LocalRefreshCadence(index_seconds=1)
        for tick in (-1, True, float("nan"), float("inf"), "1000"):
            with self.subTest(tick=str(tick)), self.assertRaises(SmartDataError):
                LocalRefreshCadence().claim_auto(
                    selected(5), SmartDataSettings(), clock(10, 30),
                    monotonic_seconds=tick, confirmed_session=True)

    def test_missing_market_session_or_disabled_auto_never_triggers(self):
        blocked=make_refresh_intent(selected(51),SmartDataSettings(),clock(10,30))
        self.assertFalse(blocked.permitted)
        disabled=make_refresh_intent(selected(5),SmartDataSettings(False,300),
                                     clock(10,30),confirmed_session=True)
        self.assertFalse(disabled.permitted)
        self.assertEqual(disabled.equity_seconds,300)
        with self.assertRaises(SmartDataError):
            make_refresh_intent(selected(5),SmartDataSettings(),clock(10,30),
                                manual="yes",confirmed_session=True)
        with self.assertRaises(SmartDataError):
            make_refresh_intent(selected(5),SmartDataSettings(),
                                datetime(2026,11,18,10,30),confirmed_session=True)

if __name__ == "__main__":
    unittest.main()
