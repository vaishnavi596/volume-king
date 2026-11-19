"""One combined 1/3/5/15/30m app-side timeframe segment regression."""
import sys
import unittest
from pathlib import Path
from datetime import datetime, timedelta, timezone

SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from app_state import LocalWatchlists
from scanner_state import ScannerSelection, choose, ScannerError, TIMEFRAMES
from candle_history import LocalCandleHistory
from historical_three_minute_fallback import HistoricalThreeMinuteFallback
from completed_timeframe_resampler import complete_session_bars
from evidence_inbox import DeviceEvidenceInbox
from feed_inbox import DeviceFeedInbox
from watchlist_parity import watchlist_row
from filter_evidence import LocalFilterEvidence

IST = timezone(timedelta(hours=5, minutes=30))
START = int(datetime(2026, 11, 18, 9, 15, tzinfo=IST).timestamp())

def bars(count=180):
    return [dict(timestamp=START + i * 60, open=100., high=102.,
                 low=99., close=101., volume=2., completed=True)
            for i in range(count)]

class FiveTimeframeTests(unittest.TestCase):
    def test_all_five_selected_and_local_save_restored(self):
        self.assertEqual(TIMEFRAMES, ("1m", "3m", "5m", "15m", "30m"))
        watchlists = LocalWatchlists()
        watchlists.add(0, "TCS")
        for tf in TIMEFRAMES:
            with self.subTest(tf=tf):
                saved = choose(ScannerSelection(), watchlists,
                               symbol="TCS", timeframe=tf)
                self.assertEqual(
                    ScannerSelection.from_saved(saved.saved_state(), watchlists),
                    saved)
        with self.assertRaises(ScannerError):
            choose(ScannerSelection(), watchlists, timeframe="45m")

    def test_all_five_validated_completed_candles(self):
        history = LocalCandleHistory()
        history.accept("TCS", "1m", 1, bars(), allowed_symbols=("TCS",))
        view = HistoricalThreeMinuteFallback(
            history, clock=lambda: START + 180 * 60)
        for tf, count in (("1m", 180), ("3m", 60), ("5m", 36),
                          ("15m", 12), ("30m", 6)):
            with self.subTest(tf=tf):
                item = view.view("TCS", tf, selected_equities=("TCS",))
                self.assertEqual(item["status"], "HIST")
                self.assertEqual(item["count"], count)
                self.assertEqual(
                    item.get("verified_live"), False if tf != "1m" else None)
                self.assertEqual(view.view("TCS", tf)["status"], "WAIT")

    def test_forming_candles_or_missing_minutes_cannot_publish(self):
        for tf, width in (("5m", 5), ("15m", 15), ("30m", 30)):
            history = LocalCandleHistory()
            source = bars(width * 2)
            history.accept("TCS", "1m", 1, source,
                           allowed_symbols=("TCS",))
            view = HistoricalThreeMinuteFallback(
                history, clock=lambda: START + width * 120 - 1)
            self.assertEqual(view.view(
                "TCS", tf, selected_equities=("TCS",))["status"], "WAIT")
            missing = source[:width + 2] + source[width + 3:]
            self.assertEqual(len(complete_session_bars(
                missing, tf, now_epoch=START + width * 120)), 1)

    def test_direct_cached_timeframe_takes_priority(self):
        history = LocalCandleHistory()
        history.accept("TCS", "1m", 1, bars(), allowed_symbols=("TCS",))
        direct = [dict(row, timestamp=START + i * 900)
                  for i, row in enumerate(bars(3))]
        history.accept("TCS", "15m", 2, direct,
                       allowed_symbols=("TCS",))
        view = HistoricalThreeMinuteFallback(
            history, clock=lambda: START + 180 * 60)
        item = view.view("TCS", "15m", selected_equities=("TCS",))
        self.assertEqual(item["count"], 3)
        self.assertNotIn("derived_from", item)

    def test_shared_watchlist_scanner_superfive_and_sixth_blank(self):
        evidence = DeviceEvidenceInbox()
        evidence.candles.accept(
            "TCS", "1m", 1, bars(), allowed_symbols=("TCS",))
        view = HistoricalThreeMinuteFallback(
            evidence.candles, clock=lambda: START + 180 * 60)
        item = watchlist_row(
            "TCS", DeviceFeedInbox(), evidence,
            selected_equities=("TCS",), history_view=view)
        self.assertIn("60 completed 3m candles HIST", item["candle"])
        filter_state = LocalFilterEvidence()
        for tf in TIMEFRAMES:
            self.assertEqual(filter_state.rows(
                "TCS", tf, selected_equities=("TCS",))[-1], ("", ""))
        source = (SRC / "main.py").read_text(encoding="utf-8")
        self.assertIn("history_view=scanner_history", source)
        self.assertIn('("1m", "3m", "5m", "15m", "30m")', source)
        self.assertIn("historical_shortlist(\n                    scanner_history", source)
        self.assertNotIn("ServerAngelFeed", source)

if __name__ == "__main__":
    unittest.main()
