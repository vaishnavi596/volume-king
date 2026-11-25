"""Watchlist must never label 5m Super Five votes as 3m candles.

Source/AST guards only; passing these tests does not prove live Dhan or phone.
"""
import ast
from pathlib import Path
import unittest

MAIN = Path(__file__).resolve().parents[1] / "src" / "main.py"


class WatchThreeMinuteContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = MAIN.read_text(encoding="utf-8")
        cls.source = source
        tree = ast.parse(source)
        cls.functions = {n.name: ast.get_source_segment(source, n)
                         for n in ast.walk(tree)
                         if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

    def test_true_three_minute_source_not_five_minute_rankings(self):
        fn = self.functions["watch_three_minute_signal"]
        self.assertIn('data=shared_history(sym,"3m")', fn)
        self.assertIn('bar[0]+180<=now', fn)
        self.assertNotIn("quality_check(", fn)
        self.assertNotIn("analyze(", fn)
        worker=self.functions["compute_watch_three_minute_worker"]
        self.assertIn('quality_check(completed,180',worker)
        self.assertIn('bars=quality["bars"]',worker)
        self.assertIn('return tuple(tuple(bar[:6]) for bar in bars),analyze(bars,selected,"3m")',worker)
        self.assertLess(worker.index('if not quality.get("usable"):'),worker.index('analyze(bars,selected,"3m")'))
        self.assertNotIn("get_market_data(", fn)
        self.assertNotIn("dhan_feed.intraday", fn)
        self.assertNotIn("watch_signal_cache", fn)

    def test_no_verified_source_shows_wait_not_fake_votes(self):
        fn = self.functions["watch_three_minute_signal"]
        self.assertIn('"bias":"WAIT"', fn)
        self.assertIn('data.get("source")!="Dhan"', fn)
        self.assertIn('"historical":True', fn)
        self.assertIn('"live_verified":False', fn)

    def test_watch_row_never_displays_legacy_5m_vote(self):
        compact = self.functions["compact_watch_signal"]
        self.assertIn('row.get("timeframe")=="3m"', compact)
        self.assertIn('vote_display(counts,False,timeframe="3m")', compact)
        self.assertNotIn('vote_display(counts,fresh)', compact)
        watch = self.functions["fill_watch"]
        self.assertIn('signal_row=watch_three_minute_signal(sym)', watch)
        self.assertIn('timeframe_spec("3m")', watch)

    def test_mounted_watchlist_tick_uses_three_minute_only(self):
        tick = self.functions["watch_visible_tick"]
        # The visible tick computes each 3m signal once and reuses it for
        # signatures, filtering and mounted cells; textual repetitions waste CPU.
        self.assertIn('tick_signals={sym:watch_three_minute_signal(sym) for sym in visible}', tick)
        self.assertIn('signal=tick_signals[sym]', tick)
        self.assertIn('signal_row=tick_signals[sym]', tick)
        self.assertIn('row=signal_row', tick)
        self.assertIn('timeframe_spec("3m")', tick)
        self.assertIn('tick_signals[sym].get("timestamp")', tick)
        self.assertNotIn('watch_signal_cache.get(sym)', tick)

    def test_super_five_shared_five_minute_path_remains(self):
        source = self.source
        self.assertIn('data=shared_history(sym) or data', source)
        self.assertIn('report_identity=(sym,"5m",identity)', source)
        shared = self.functions["refresh_shared_analysis"]
        ranking = self.functions["rank_one"]
        self.assertIn('engine_snapshot=await local_analysis_pool.run(scanner_snapshot_with_candle,', shared)
        self.assertIn('deepcopy(result),snapshot,symbol=sym,timeframe="5m",now=time.time()', shared)
        self.assertIn('publish_five_engine_5m(sym,engine_snapshot)',shared)
        self.assertIn('engine_snapshot=await local_analysis_pool.run(scanner_snapshot_with_candle,', ranking)
        self.assertIn('deepcopy(engine_input),deepcopy(data),symbol=sym,timeframe="5m",', ranking)
        self.assertIn('now=time.time(),timing=engine_timing)', ranking)
        self.assertIn('source="Dhan" if source_ok else ""', ranking)
        self.assertIn('live_verified=verified,historical=not verified', ranking)
        after=ranking.split('engine_snapshot=await local_analysis_pool.run(',1)[1]
        guard=after.split('publish_five_engine_5m(sym,engine_snapshot)',1)[0]
        self.assertIn('generation!=provider_generation[0]', guard)
        self.assertIn('engine_policy!=', guard)
        self.assertIn('return sym,None', guard)
        self.assertIn('publish_five_engine_5m(sym,engine_snapshot)', after)
        self.assertNotIn('scanner_snapshot_with_candle', self.functions["watch_three_minute_signal"])
        self.assertIn('symbol=sym,timeframe="5m",generation=provider_generation[0]', source)


if __name__ == "__main__":
    unittest.main()
