"""Offline scanner candle safety regression."""
import math, sys, unittest
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scanner_engine import analyze, rank_candidates

def candles():
    start = int(datetime.now(timezone.utc).timestamp()) - 35 * 300
    return [[start + i * 300, 100., 102., 99., 101., 1000.] for i in range(35)]

class ScannerSafetyTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(analyze(candles())["count"], 35)
    def test_duplicate_timestamp(self):
        b = candles(); b[-1][0] = b[-2][0]
        r = analyze(b)
        self.assertEqual(r["bias"], "WAIT")
        self.assertIsNone(r["timestamp"])
    def test_reversed_timestamp(self):
        b = candles(); b[-1][0] = b[-2][0] - 1
        self.assertEqual(analyze(b)["bias"], "WAIT")
    def test_impossible_ohlc(self):
        b = candles(); b[-1][2] = 90.
        self.assertEqual(analyze(b)["count"], 34)
    def test_nan(self):
        b = candles(); b[-1][4] = math.nan
        self.assertEqual(analyze(b)["count"], 34)
    def test_malformed_bar_ignored(self):
        b = candles(); b[-1] = None
        self.assertEqual(analyze(b)["count"], 34)
    def test_invalid_ranking_vote_is_excluded(self):
        now = datetime.now(timezone.utc).timestamp()
        r = {"bias":"BULLISH","timestamp":now,"count":35,"score":95,"votes":[{"name":"EMA 9/21","vote":1},{"name":"MACD","vote":1},{"name":"RSI 14","vote":-1}]}
        self.assertEqual(rank_candidates({"ABC":r}), [])
    def test_ranking_ties_are_deterministic(self):
        now = datetime.now(timezone.utc).timestamp()
        r = {"bias":"BULLISH","timestamp":now,"count":35,"score":100,"votes":[{"name":"EMA 9/21","vote":1},{"name":"MACD","vote":1},{"name":"RSI 14","vote":1}]}
        self.assertEqual([x["symbol"] for x in rank_candidates({"ZZZ":r,"AAA":r})], ["AAA","ZZZ"])
    def test_future_candle_excluded(self):
        b = candles(); b[-1][0] = datetime.now(timezone.utc).timestamp() + 3600
        self.assertEqual(analyze(b)["count"], 34)
    def test_invalid_freshness_limit(self):
        self.assertEqual(rank_candidates({}, max_age_seconds=float("nan")), [])
    def test_inflated_ranking_score(self):
        r = {"bias":"BULLISH","timestamp":datetime.now(timezone.utc).timestamp(),"count":35,"score":100,"votes":[{"name":"EMA 9/21","vote":1},{"name":"MACD","vote":1},{"name":"RSI 14","vote":1},{"name":"VWAP","vote":-1}]}
        self.assertEqual(rank_candidates({"ABC":r}), [])
    def test_intraday_gap_blocks_signal(self):
        b = candles()
        # Fixed same-session bars avoid midnight-dependent test behavior.
        from datetime import timedelta
        ist = timezone(timedelta(hours=5, minutes=30))
        start = datetime(2026, 11, 11, 9, 15, tzinfo=ist).timestamp()
        for i, bar in enumerate(b): bar[0] = start + i * 300
        b[20][0] += 600
        for i in range(21, len(b)): b[i][0] += 600
        self.assertEqual(analyze(b)["bias"], "WAIT")
    def test_overnight_gap_is_allowed(self):
        b = candles()
        from datetime import timedelta
        ist = timezone(timedelta(hours=5, minutes=30))
        first = datetime(2026, 11, 10, 14, 0, tzinfo=ist).timestamp()
        second = datetime(2026, 11, 11, 9, 15, tzinfo=ist).timestamp()
        for i, bar in enumerate(b): bar[0] = first + i * 300 if i < 10 else second + (i - 10) * 300
        self.assertEqual(analyze(b)["count"], 35)
    def test_missing_vote_key_does_not_crash(self):
        r = {"bias":"BULLISH","timestamp":datetime.now(timezone.utc).timestamp(),"count":35,"score":100,"votes":[{"name":"EMA 9/21"},{"name":"MACD","vote":1},{"name":"RSI 14","vote":1}]}
        self.assertEqual(rank_candidates({"ABC":r}), [])
    def test_boolean_vote_is_rejected(self):
        r = {"bias":"BULLISH","timestamp":datetime.now(timezone.utc).timestamp(),"count":35,"score":100,"votes":[{"name":"EMA 9/21","vote":True},{"name":"MACD","vote":1},{"name":"RSI 14","vote":1}]}
        self.assertEqual(rank_candidates({"ABC":r}), [])
    def test_invalid_ranking_inputs_are_safe(self):
        self.assertEqual(rank_candidates(None), [])
        self.assertEqual(rank_candidates({}, max_results=0), [])
    def test_explicit_unverified_data_not_ranked(self):
        r = {"bias":"BULLISH","timestamp":datetime.now(timezone.utc).timestamp(),"count":35,"score":100,"freshness":"unverified","votes":[{"name":"EMA 9/21","vote":1},{"name":"MACD","vote":1},{"name":"RSI 14","vote":1}]}
        self.assertEqual(rank_candidates({"ABC":r}), [])
    def test_duplicate_indicator_cannot_inflate_votes(self):
        r = {"bias":"BULLISH","timestamp":datetime.now(timezone.utc).timestamp(),"count":35,"score":100,"votes":[{"name":"EMA 9/21","vote":1},{"name":"EMA 9/21","vote":1},{"name":"EMA 9/21","vote":1}]}
        self.assertEqual(rank_candidates({"ABC":r}), [])
    def test_insufficient_ranking(self):
        r = {"bias":"BULLISH","timestamp":datetime.now(timezone.utc).timestamp(),"count":5,"score":99,"votes":[]}
        self.assertEqual(rank_candidates({"ABC":r}), [])

if __name__ == "__main__":
    unittest.main()
