"""Consolidated safe migration regression: offline V1 candle helpers in active V2."""
import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
from candle_history import LocalCandleHistory
from historical_migration import three_minute_from_local_history
from candle_retention import retain_candle_history, retain_last_filter_votes
from analysis_quality import quality_check

IST = timezone(timedelta(hours=5, minutes=30))

class SafeMigrationTests(unittest.TestCase):
    def test_exact_three_minute_completed_offline(self):
        start = int(datetime(2026, 11, 18, 9, 15, tzinfo=IST).timestamp())
        bars = [dict(timestamp=start + i*60, open=100., high=102., low=99.,
                     close=101., volume=10., completed=True) for i in range(3)]
        history = LocalCandleHistory()
        self.assertTrue(history.accept("TCS", "1m", 1, bars, allowed_symbols=("TCS",)))
        self.assertEqual(three_minute_from_local_history(history, "TCS",
                         selected_equities=("TCS",), now_epoch=start+180)["status"], "HIST")
        self.assertEqual(len(three_minute_from_local_history(history, "TCS",
                         selected_equities=("TCS",), now_epoch=start+179)["bars"]), 0)
        self.assertEqual(three_minute_from_local_history(history, "TCS",
                         selected_equities=(), now_epoch=start+180)["status"], "WAIT")

    def test_last_good_history_never_claims_live(self):
        old = [[1000+i*60, 100., 101., 99., 100., 10.] for i in range(30)]
        prior = {"source":"Dhan","bars":old,"candle_fetched_at":2000}
        incoming = {"source":"Dhan","bars":[],"freshness":"verified_live"}
        result = retain_candle_history(incoming, prior)
        self.assertTrue(result["historical"])
        self.assertFalse(result["live_verified"])
        self.assertEqual(result["freshness"], "historical_unverified")
        self.assertEqual(retain_candle_history({"source":"Yahoo","bars":[]}, prior)["bars"], [])

    def test_missing_votes_not_promoted(self):
        old = {"source":"Dhan","votes":[{"name":"x","vote":1}],"timestamp":1000}
        result = retain_last_filter_votes({"source":"Dhan","votes":[]},old,selected_filters=("x",))
        self.assertEqual(result["bias"], "WAIT")
        self.assertFalse(result["live_verified"])

    def test_quality_rejects_future_or_invalid(self):
        now = 100000
        bars = [[now-2000+i*60, 100, 101, 99, 100, 10] for i in range(30)]
        self.assertTrue(quality_check(bars, 60, now=now)["usable"])
        bars[-1][3] = 105
        self.assertFalse(quality_check(bars, 60, now=now)["usable"])

if __name__ == "__main__":
    unittest.main()
