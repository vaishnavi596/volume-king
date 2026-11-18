"""Offline V2 FT3 exact completed-candle / direction-evidence join."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(ROOT))
from candle_history import LocalCandleHistory, CandleEvidenceError
from filter_evidence import LocalFilterEvidence, FilterEvidenceError
from candle_filter_gate import accept_candle_trend


def bars(last=200):
    return [
        {"timestamp": 100, "open": 100, "high": 102, "low": 99,
         "close": 101, "volume": 5, "completed": True},
        {"timestamp": last, "open": 101, "high": 103, "low": 100,
         "close": 102, "volume": 6, "completed": True},
    ]


def trend(t=200, direction="bullish"):
    return {"direction": direction, "source": "dhan",
            "observed_at": t, "eligible": True}


class CandleFilterJoinTests(unittest.TestCase):
    def setUp(self):
        self.candles = LocalCandleHistory()
        self.filters = LocalFilterEvidence()

    def accept(self, symbol="NIFTY", timeframe="1m", revision=1,
               evidence=None, selected=(), trusted=True):
        return accept_candle_trend(
            self.candles, self.filters, symbol, timeframe, revision,
            trend() if evidence is None else evidence,
            selected_equities=selected, trusted_transport=trusted)

    def test_requires_completed_history_and_trusted_transport(self):
        with self.assertRaises(CandleEvidenceError):
            self.accept()
        self.candles.accept("NIFTY", "1m", 1, bars(), allowed_symbols=("NIFTY",))
        with self.assertRaises(FilterEvidenceError):
            self.accept(trusted=False)
        self.assertEqual(self.filters.rows("NIFTY", "1m")[4][1], "WAIT")

    def test_matching_final_bar_allows_only_candle_factor_and_sixth_stays_blank(self):
        self.candles.accept("NIFTY", "1m", 1, bars(), allowed_symbols=("NIFTY",))
        self.assertTrue(self.accept())
        rows = self.filters.rows("NIFTY", "1m")
        self.assertEqual([v for _, v in rows[:5]],
                         ["WAIT", "WAIT", "WAIT", "WAIT", "BULLISH HIST"])
        self.assertEqual(rows[5], ("", ""))
        self.assertFalse(self.accept())  # No duplicate revision.

    def test_replayed_or_wrong_timeframe_observation_never_overwrites(self):
        self.candles.accept("NIFTY", "1m", 1, bars(), allowed_symbols=("NIFTY",))
        self.assertTrue(self.accept())
        for context in (
            {"timeframe": "3m", "evidence": trend()},
            {"timeframe": "1m", "evidence": trend(100, "bearish")},
            {"timeframe": "1m", "evidence": trend(300, "bearish")},
            {"timeframe": "1m", "evidence": dict(trend(), source="yahoo")},
        ):
            with self.subTest(context=context), self.assertRaises((CandleEvidenceError, FilterEvidenceError)):
                self.accept(revision=2, **context)
        self.assertEqual(self.filters.rows("NIFTY", "1m")[4][1], "BULLISH HIST")
        self.candles.accept("NIFTY", "1m", 2, bars(last=300),
                            allowed_symbols=("NIFTY",))
        self.assertTrue(self.accept(revision=2, evidence=trend(300, "bearish")))
        self.assertEqual(self.filters.rows("NIFTY", "1m")[4][1], "BEARISH HIST")

    def test_removed_equity_and_index_independence(self):
        self.candles.accept("TCS", "3m", 1, bars(), allowed_symbols=("TCS",))
        self.assertTrue(self.accept("TCS", "3m", selected=("TCS",)))
        self.assertEqual(self.filters.rows("TCS", "3m", selected_equities=("TCS",))[4][1], "BULLISH HIST")
        with self.assertRaises(FilterEvidenceError):
            self.accept("TCS", "3m")
        self.assertEqual(self.filters.rows("TCS", "3m")[4][1], "WAIT")
        self.candles.forget_removed(())
        self.filters.forget_removed(())
        self.assertEqual(self.filters.rows("TCS", "3m", selected_equities=("TCS",))[4][1], "WAIT")
        self.assertEqual(self.filters.rows("BANKNIFTY", "1m")[4][1], "WAIT")


if __name__ == "__main__":
    unittest.main()
