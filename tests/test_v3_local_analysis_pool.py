import asyncio
import unittest
from v3_local_analysis_pool import LocalAnalysisPool, worker_budget

class LocalPoolTests(unittest.TestCase):
    def test_budget_reserves_capacity(self):
        self.assertEqual(worker_budget(1, 8*1024**3),1)
        self.assertEqual(worker_budget(8, 8*1024**3),7)
        self.assertEqual(worker_budget(16, 256*1024**2),1)
        self.assertEqual(worker_budget(32, 32*1024**3),8)
    def test_results_and_failure_telemetry(self):
        pool=LocalAnalysisPool(2)
        def fail():
            raise ValueError("fixture")
        async def run():
            self.assertEqual(await asyncio.gather(*(pool.run(pow,n,2) for n in range(70))),[n*n for n in range(70)])
            with self.assertRaises(ValueError):
                await pool.run(fail)
        try:
            asyncio.run(run())
            stats=pool.diagnostics()
            self.assertEqual(stats["completed"],71)
            self.assertEqual(stats["failed"],1)
            self.assertEqual(stats["pending"],0)
            self.assertEqual(stats["running"],0)
            self.assertEqual(stats["provider_requests"],0)
        finally:pool.close()

    def test_super_five_worker_keeps_publication_on_app_lane(self):
        import ast
        from pathlib import Path
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        tree=ast.parse(source)
        rank=next(n for n in ast.walk(tree) if isinstance(n,ast.AsyncFunctionDef) and n.name=="rank_one")
        body=ast.get_source_segment(source,rank)
        worker="result=await local_analysis_pool.run(display_analysis,sym,snapshot,frozen=frozen)"
        self.assertIn(worker,body)
        before,after=body.split(worker,1)
        self.assertIn('snapshot=dict(data,bars=[tuple(row)',before)
        guard=after.split("record_analysis(",1)[0]
        self.assertIn("generation!=provider_generation[0]",guard)
        self.assertIn("frozen!=",guard)
        self.assertIn("return sym,None",guard)
        self.assertIn("publish_five_engine_5m",after)
        display=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="display_analysis")
        self.assertIn('if frozen is None:record_analysis',ast.get_source_segment(source,display))

    def test_watchlist_worker_rechecks_identity_before_publication(self):
        import ast
        from pathlib import Path
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        tree=ast.parse(source)
        funcs={n.name:n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        body=ast.get_source_segment(source,funcs["prepare_watch_three_minute_signal"])
        worker="result=await local_analysis_pool.run(compute_watch_three_minute_worker,completed,selected)"
        self.assertIn(worker,body)
        before,after=body.split(worker,1)
        self.assertIn("saved[0]==identity:return",before)
        self.assertIn("latest is None or latest[0]!=identity:return",after.split("watch_three_minute_cache[sym]",1)[0])
        self.assertIn("live_verified=False",after)
        self.assertIn('publish_five_engine_historical(sym,"3m",result)',after)
        capture=ast.get_source_segment(source,funcs["watch_three_minute_worker_input"])
        self.assertIn("provider_generation[0]",capture)
        self.assertIn("tuple(completed[-4:])",capture)
        self.assertIn('bar[0]+180<=now',capture)
        tick=ast.get_source_segment(source,funcs["watch_visible_tick"])
        self.assertIn("await asyncio.gather(*(prepare_watch_three_minute_signal(sym) for sym in visible))",tick)
        self.assertIn("tick_generation!=provider_generation[0]",tick)
        self.assertIn("visible!=tuple(watch_groups[active_watch[0]])",tick)

    def test_engine_adapter_timing_does_not_change_vote_or_invent_work(self):
        from five_engine import scanner_snapshot_with_candle
        timing={}
        args=dict(symbol="NIFTY",timeframe="5m",now=1000)
        baseline=scanner_snapshot_with_candle({}, {}, **args)
        actual=scanner_snapshot_with_candle({}, {}, timing=timing, **args)
        self.assertEqual(baseline,actual)
        self.assertEqual(actual["combined"]["state"],"WAIT")
        self.assertGreaterEqual(timing["technical_adapter_ms"],0)
        self.assertGreaterEqual(timing["compose_vote_ms"],0)
        self.assertFalse(timing["candle_checked"])
        for key in ("candle_adapter_ms","news_adapter_ms","futures_adapter_ms","options_adapter_ms"):
            self.assertIsNone(timing[key])

    def test_remaining_scanner_and_ranking_writes_are_awaited(self):
        import ast
        from pathlib import Path
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        tree=ast.parse(source)
        funcs={n.name:n for n in ast.walk(tree) if isinstance(n,ast.AsyncFunctionDef)}
        scan=ast.get_source_segment(source,funcs["scan_market"])
        self.assertEqual(scan.count('await asyncio.to_thread(market_store.put,"analysis",'),2)
        self.assertEqual(scan.count('await asyncio.to_thread(market_store.put,"analysis_last_good",'),1)
        self.assertNotIn('market_store.put("analysis',scan)
        for part in scan.split('await asyncio.to_thread(market_store.put,"analysis')[1:]:
            guard=part.split('):return',1)[0]
            for check in ("generation!=scan_generation[0]","sym!=scan_symbol.value","interval!=scan_tf.value","provider_generation[0]"):
                self.assertIn(check,guard)
        retry=ast.get_source_segment(source,funcs["retry_failed_symbol"])
        self.assertIn('await asyncio.to_thread(market_store.put,"ranking"',retry)
        self.assertIn("if generation!=provider_generation[0]:return",retry.split('await asyncio.to_thread(market_store.put,"ranking"',1)[1])
        self.assertEqual(source.count('await asyncio.to_thread(market_store.put,"ranking"'),2)
        self.assertNotIn('market_store.put("ranking"',source)
