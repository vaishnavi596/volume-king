"""Synthetic, no-network tests for BOT KING historical memory contract."""
import unittest
from src.market_memory import MarketSession, remember_session, analyze_memory


def session(day, close=100.0, *, symbol="NIFTY", volume=100.0):
    return MarketSession(symbol=symbol, day=day, open=100.0,
                         high=max(101.0, close), low=min(99.0, close),
                         close=close, volume=volume)


class MarketMemoryTests(unittest.TestCase):
    def test_only_completed_dhan_sessions_accepted(self):
        with self.assertRaises(ValueError):
            MarketSession("NIFTY", "2026-11-16", 100, 101, 99, 100, 1,
                          source="Yahoo")
        with self.assertRaises(ValueError):
            MarketSession("NIFTY", "2026-11-16", 100, 101, 99, 100, 1,
                          completed=False)
        with self.assertRaises(ValueError):
            MarketSession("NIFTY", "2026-11-16", 100, 101, 99, 100, 1,
                          explanation="Market went up because of news")

    def test_bounded_idempotent_sessions_and_conflict(self):
        history = ()
        for d in range(1, 9):
            history = remember_session(history, session(f"2026-11-{d:02d}"),
                                       max_sessions=5)
        self.assertEqual(len(history), 5)
        self.assertEqual(history[0].day, "2026-11-04")
        self.assertEqual(remember_session(history, history[-1], max_sessions=5),
                         history)
        with self.assertRaises(ValueError):
            remember_session(history, session("2026-11-08", close=101),
                             max_sessions=5)

    def test_no_future_leakage_or_fake_scores(self):
        rows = tuple(session(f"2026-11-{d:02d}", close=100 + d)
                     for d in range(1, 9))
        output = analyze_memory(rows, symbol="NIFTY", as_of="2026-11-07")
        self.assertEqual(output["sample_end"], "2026-11-06")
        self.assertIsNone(output["bullish_score"])
        self.assertIsNone(output["forecast_probability"])
        self.assertFalse(output["signal_eligible"])
        self.assertFalse(output["causal_explanation_verified"])

    def test_range_and_volume_are_observations_not_causes(self):
        rows = [session(f"2026-11-{d:02d}") for d in range(1, 6)]
        rows.append(MarketSession("NIFTY", "2026-11-06", 100, 118, 98, 115, 300))
        output = analyze_memory(rows, symbol="NIFTY", as_of="2026-11-07")
        self.assertIn("Latest completed session volume above its historical median",
                      output["observations"])
        self.assertIn("Latest close above preceding observed highs",
                      output["observations"])
        self.assertEqual(output["status"], "HISTORICAL_CONTEXT")

    def test_insufficient_history_and_symbol_isolation(self):
        output = analyze_memory((session("2026-11-01"),), symbol="NIFTY",
                                as_of="2026-11-03")
        self.assertEqual(output["status"], "INSUFFICIENT_HISTORY")
        with self.assertRaises(ValueError):
            remember_session((session("2026-11-01"),),
                             session("2026-11-03", symbol="TCS"))
        with self.assertRaises(ValueError):
            analyze_memory((session("2026-11-01", symbol="TCS"),),
                           symbol="NIFTY", as_of="2026-11-03")

    def test_invalid_ohlc_and_nan_rejected(self):
        with self.assertRaises(ValueError):
            session("2026-11-01", close=float("nan"))
        with self.assertRaises(ValueError):
            MarketSession("NIFTY", "2026-11-01", 100, 99, 98, 101, 1)


if __name__ == "__main__":
    unittest.main()
