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
        worker="computed=await local_analysis_pool.run(compute_watch_three_minute_worker,completed,selected)"
        self.assertIn(worker,body)
        before,after=body.split(worker,1)
        self.assertIn("saved[0]==identity:return",before)
        self.assertIn("latest is None or latest[0]!=identity:return",after.split("watch_three_minute_cache[sym]",1)[0])
        self.assertLess(after.index("latest is None or latest[0]!=identity:return"),after.index("historical_indicator_cache[cache_key]=result"))
        self.assertLess(after.index("historical_indicator_cache[cache_key]=result"),after.index("result=dict(result,source="))
        self.assertIn("live_verified=False",after)
        self.assertIn('publish_five_engine_historical(sym,"3m",result)',after)
        capture=ast.get_source_segment(source,funcs["watch_three_minute_worker_input"])
        self.assertIn("provider_generation[0]",capture)
        self.assertIn("tuple(completed[-4:])",capture)
        self.assertIn('bar[0]+180<=now',capture)
        tick=ast.get_source_segment(source,funcs["watch_visible_tick"])
        self.assertIn("visible[offset:offset+local_analysis_pool.workers]",tick)
        self.assertIn("tick_generation==provider_generation[0]",tick)
        self.assertIn("visible==tuple(watch_groups[active_watch[0]])",tick)

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
        persist=ast.get_source_segment(source,funcs["persist_current_ranking"])
        self.assertIn("await persist_current_ranking(retry_owner_current,roster,",retry)
        self.assertIn("if not retry_owner_current():return",retry.split("await persist_current_ranking(",1)[1])
        self.assertIn('await asyncio.to_thread(market_store.put,"ranking"',persist)
        self.assertIn("async with ranking_persist_lock:",persist)
        self.assertIn("if not owner_current():",persist.split('await asyncio.to_thread(market_store.put,"ranking"',1)[1])
        self.assertEqual(source.count('await asyncio.to_thread(market_store.put,"ranking"'),1)
        self.assertNotIn('market_store.put("ranking"',source)

    def test_watchlist_offscreen_worker_and_single_flight(self):
        from pathlib import Path
        import ast
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        funcs={n.name:ast.get_source_segment(source,n) for n in ast.walk(ast.parse(source)) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        reader=funcs["watch_three_minute_signal"]
        self.assertNotIn("analyze(",reader)
        self.assertNotIn("quality_check(",reader)
        worker=funcs["prepare_watch_three_minute_signal"]
        self.assertIn("if key in watch_three_minute_inflight:return",worker)
        self.assertIn("finally:",worker)
        self.assertIn("watch_three_minute_inflight.discard(key)",worker)
        loop=funcs["watch_all_local_analysis"]
        self.assertIn("all_watch_symbols()",loop)
        self.assertIn("local_analysis_pool.workers",loop)
        self.assertIn("lifecycle_background[0]",loop)
        self.assertNotIn("get_market_data(",loop)
        self.assertIn("page.run_task(watch_all_local_analysis)",source)

    def test_engine_snapshot_worker_preserves_vote_and_publish_guard(self):
        import ast
        from pathlib import Path
        from five_engine import scanner_snapshot_with_candle
        pool=LocalAnalysisPool(2)
        try:
            inputs=dict(symbol="NIFTY",timeframe="5m",now=1000)
            timing={}
            actual=asyncio.run(pool.run(scanner_snapshot_with_candle,{}, {},timing=timing,**inputs))
            self.assertEqual(actual,scanner_snapshot_with_candle({}, {},**inputs))
            self.assertEqual(actual["combined"]["state"],"WAIT")
        finally:pool.close()
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        rank=next(n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.AsyncFunctionDef) and n.name=="rank_one")
        body=ast.get_source_segment(source,rank)
        before,after=body.split("engine_snapshot=await local_analysis_pool.run(scanner_snapshot_with_candle,",1)
        guard=after.split("publish_five_engine_5m(sym,engine_snapshot)",1)[0]
        self.assertIn("deepcopy(engine_input),deepcopy(data)",guard)
        self.assertIn("generation!=provider_generation[0]",guard)
        self.assertIn("engine_policy!=",guard)
        self.assertIn("return sym,None",guard)

    def test_shared_and_retry_analysis_are_awaited(self):
        import ast
        from pathlib import Path
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        funcs={n.name:ast.get_source_segment(source,n) for n in ast.walk(ast.parse(source)) if isinstance(n,ast.AsyncFunctionDef)}
        shared=funcs["refresh_shared_analysis"]
        self.assertIn("await local_analysis_pool.run(display_analysis,sym,snapshot,frozen=frozen)",shared)
        self.assertIn("await local_analysis_pool.run(scanner_snapshot_with_candle,",shared)
        self.assertIn("shared_history(sym)!=snapshot",shared)
        self.assertIn("publish_five_engine_5m(sym,engine_snapshot)",shared)
        retry=funcs["retry_failed_symbol"]
        self.assertIn("await local_analysis_pool.run(display_analysis,symbol,snapshot,frozen=frozen)",retry)
        self.assertIn("generation==provider_generation[0]",retry)
        self.assertIn("if not retry_owner_current():return",retry)
        self.assertIn("if (not retry_owner_current() or frozen!=",retry)
        for check in ('prefs.get("source")==source',"app_active[0]","not lifecycle_background[0]","set(roster)==set(all_watch_symbols())"):
            self.assertIn(check,retry)

    def test_super_five_local_observer_offloads_and_rejects_stale_revision(self):
        import ast
        from pathlib import Path
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        node=next(n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.AsyncFunctionDef) and n.name=="super_five_minute_refresh")
        body=ast.get_source_segment(source,node)
        worker="await local_analysis_pool.run(display_analysis,sym,snapshot,frozen=frozen)"
        self.assertIn(worker,body)
        self.assertIn("tuple(tuple(row) for row in bars)",body)
        self.assertIn("snapshot=deepcopy(data)",body)
        guard=body.split(worker,1)[1].split("publish_partial_ranking(results)",1)[0]
        for check in ("generation!=provider_generation[0]","policy()!=selected_policy","revision(capture())!=fingerprint[-1]","current[0]!=0"):
            self.assertIn(check,guard)
        self.assertIn("record_analysis",guard)
        self.assertNotIn("get_market_data(",body)


    def test_cancel_running_worker_retains_owner_until_thread_exits(self):
        from threading import Event
        pool=LocalAnalysisPool(1)
        started=Event()
        release=Event()
        owners=set()
        def work():
            started.set()
            if not release.wait(5):
                raise RuntimeError("fixture timeout")
        async def caller():
            owners.add("same-analysis")
            try:
                await pool.run(work)
            finally:
                owners.discard("same-analysis")
        async def check():
            task=asyncio.create_task(caller())
            try:
                self.assertTrue(await asyncio.to_thread(started.wait,2))
                task.cancel()
                await asyncio.sleep(0)
                self.assertFalse(task.done())
                self.assertIn("same-analysis",owners)
                task.cancel()
                await asyncio.sleep(0)
                self.assertIn("same-analysis",owners)
                release.set()
                with self.assertRaises(asyncio.CancelledError):
                    await asyncio.wait_for(task,2)
                self.assertFalse(owners)
                stats=pool.diagnostics()
                self.assertEqual(stats["running"],0)
                self.assertEqual(stats["running_cancel_waits"],1)
            finally:
                release.set()
                await asyncio.gather(task,return_exceptions=True)
        try:
            asyncio.run(check())
        finally:
            pool.close()

    def test_cancel_queued_worker_does_not_execute(self):
        from threading import Event
        pool=LocalAnalysisPool(1)
        started=Event()
        release=Event()
        calls=[]
        def work():
            started.set()
            release.wait(5)
        async def check():
            first=asyncio.create_task(pool.run(work))
            second=None
            try:
                self.assertTrue(await asyncio.to_thread(started.wait,2))
                second=asyncio.create_task(pool.run(lambda:calls.append("unexpected")))
                await asyncio.sleep(0)
                self.assertEqual(pool.diagnostics()["pending"],1)
                second.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await second
                self.assertEqual(pool.diagnostics()["pending"],0)
                self.assertEqual(pool.diagnostics()["cancelled"],1)
                self.assertFalse(calls)
            finally:
                release.set()
                await first
                if second is not None:
                    await asyncio.gather(second,return_exceptions=True)
        try:
            asyncio.run(check())
        finally:
            pool.close()


    def test_worker_cpu_and_process_rss_measurements_are_truthful(self):
        from unittest.mock import patch, mock_open
        import time
        pool=LocalAnalysisPool(1)
        try:
            with patch("builtins.open",mock_open(read_data="VmRSS: 1234 kB\n")):
                initial=pool.diagnostics()
                self.assertEqual(initial["process_rss_bytes"],1234*1024)
                self.assertIsNone(initial["thread_cpu_total_ms"])
            self.assertEqual(asyncio.run(pool.run(sum,range(10000))),49995000)
            with patch("builtins.open",side_effect=OSError("unsupported")):
                stats=pool.diagnostics()
                self.assertIsNone(stats["process_rss_bytes"])
                self.assertEqual(stats["provider_requests"],0)
                if hasattr(time,"thread_time"):
                    self.assertEqual(stats["thread_cpu_samples"],1)
                    self.assertGreaterEqual(stats["thread_cpu_total_ms"],0)
                    self.assertGreaterEqual(stats["thread_cpu_last_ms"],0)
        finally:
            pool.close()

    def test_rank_worker_rechecks_owner_and_exact_input_before_publication(self):
        import ast
        from pathlib import Path
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        rank=next(n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.AsyncFunctionDef) and n.name=="rank_one")
        body=ast.get_source_segment(source,rank)
        self.assertIn("captured=deepcopy(data)",body)
        self.assertIn("sym in all_watch_symbols()",body)
        self.assertIn("(shared_history(sym) or cycle_data.get(sym))==captured",body)
        final=body.split("engine_snapshot=await local_analysis_pool.run(",1)[1]
        for write in ('record_analysis(', 'ranking_results[sym]=result', 'watch_signal_cache[sym]', 'publish_five_engine_5m('):
            self.assertLess(final.index("if not input_current():return sym,None"),final.index(write))
        self.assertNotIn("ranking_results[sym]=result",body.split("engine_snapshot=await",1)[0])
        owner=next(n for n in ast.walk(rank) if isinstance(n,ast.FunctionDef) and n.name=="owner_current")
        guard=next(n for n in ast.walk(rank) if isinstance(n,ast.FunctionDef) and n.name=="input_current")
        from types import SimpleNamespace
        captured={"bars":[[1,2,3,4,5,6]]}
        latest={"bars":[[1,2,3,4,5,6]]}
        roster=["TCS"]
        env=dict(generation=1,provider_generation=[1],app_active=[True],lifecycle_background=[False],prefs={"source":"Dhan"},dhan_feed=SimpleNamespace(connected=True),sym="TCS",all_watch_symbols=lambda:roster,captured=captured,shared_history=lambda sym:latest,cycle_data={})
        exec(compile(ast.Module(body=[owner,guard],type_ignores=[]),"<rank guards>","exec"),env)
        self.assertTrue(env["input_current"]())
        latest["bars"][0][-1]=7
        self.assertFalse(env["input_current"]())
        latest["bars"][0][-1]=6
        roster.clear()
        self.assertFalse(env["input_current"]())
        roster.append("TCS")
        env["provider_generation"][0]=2
        self.assertFalse(env["input_current"]())
        env["provider_generation"][0]=1
        env["dhan_feed"].connected=False
        self.assertFalse(env["input_current"]())

    def test_rank_aggregate_rejects_stale_owner_and_detached_news(self):
        import ast
        from pathlib import Path
        from types import SimpleNamespace
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        tree=ast.parse(source)
        guard=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="ranking_owner_current")
        roster=["TCS"]
        env=dict(generation=1,provider_generation=[1],prefs={"source":"Dhan"},app_active=[True],lifecycle_background=[False],dhan_feed=SimpleNamespace(connected=True),ranking_symbols=["TCS"],all_watch_symbols=lambda:roster)
        exec(compile(ast.Module(body=[guard],type_ignores=[]),"<aggregate owner>","exec"),env)
        self.assertTrue(env["ranking_owner_current"]())
        roster.append("INFY")
        self.assertFalse(env["ranking_owner_current"]())
        roster.pop()
        env["lifecycle_background"][0]=True
        self.assertFalse(env["ranking_owner_current"]())
        env["lifecycle_background"][0]=False
        env["provider_generation"][0]=2
        self.assertFalse(env["ranking_owner_current"]())
        self.assertIn('persist=False),timeout=20)',source)
        self.assertIn('if not any(row is candidate for row in top5_candidates):continue',source)
        self.assertIn('if available and ranking_owner_current():',source)

    def test_ranking_persistence_serializes_and_restores_historical_only(self):
        import ast
        from pathlib import Path
        from types import SimpleNamespace
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        node=next(n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.AsyncFunctionDef) and n.name=="persist_current_ranking")
        writes=[]
        current=[True]
        row={"symbol":"TCS","source":"Dhan","bias":"BULLISH","live_verified":True}
        removed=dict(row,symbol="INFY")
        async def check():
            stats={"skipped_owner":0,"saved":0,"failed":0}
            lock=asyncio.Lock()
            env=dict(asyncio=asyncio,ranking_persist_lock=lock,ranking_persist_stats=stats,
                     prefs={"source":"Dhan"},top5_candidates=[row,removed],
                     watch_signal_cache={"TCS":row,"INFY":removed},
                     market_store=SimpleNamespace(put=lambda *args: writes.append(args) or True))
            exec(compile(ast.Module(body=[node],type_ignores=[]),"<ranking persistence>","exec"),env)
            persist=env["persist_current_ranking"]
            async with lock:
                task=asyncio.create_task(persist(lambda:current[0],["TCS"],"now"))
                await asyncio.sleep(0)
                current[0]=False
            self.assertFalse(await task)
            self.assertFalse(writes)
            current[0]=True
            self.assertTrue(await persist(lambda:current[0],["TCS"],"now"))
            payload=writes[0][2]
            for key in ("rows","all_rows"):
                self.assertEqual([r["symbol"] for r in payload[key]],["TCS"])
                self.assertTrue(payload[key][0]["historical"])
                self.assertFalse(payload[key][0]["live_verified"])
            self.assertTrue(row["live_verified"])
            self.assertEqual(stats,{"skipped_owner":1,"saved":1,"failed":0})
        asyncio.run(check())
        self.assertIn("await persist_current_ranking(retry_owner_current,roster,",source)
        self.assertIn("await persist_current_ranking(ranking_owner_current,ranking_symbols,",source)
        self.assertIn('data["ranking_persistence"]=dict(ranking_persist_stats)',source)

    def test_selected_fusion_owner_rejects_provider_policy_and_lifecycle_changes(self):
        import ast
        from pathlib import Path
        from types import SimpleNamespace
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        tree=ast.parse(source)
        guard=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="selected_fusion_owner")
        filters=["one"]
        env=dict(scan_generation=[2],provider_generation=[3],scan_symbol=SimpleNamespace(value="TCS"),
                 scan_tf=SimpleNamespace(value="3m"),active_analysis_filters=lambda:filters,
                 prefs={"source":"Dhan","confidence":75},app_active=[True],
                 lifecycle_background=[False],dhan_feed=SimpleNamespace(connected=True))
        exec(compile(ast.Module(body=[guard],type_ignores=[]),"<fusion owner>","exec"),env)
        def current():return env["selected_fusion_owner"]("TCS","3m",2,3,["one"],75)
        self.assertTrue(current())
        env["provider_generation"][0]=4
        self.assertFalse(current())
        env["provider_generation"][0]=3
        filters.append("two")
        self.assertFalse(current())
        filters.pop()
        env["lifecycle_background"][0]=True
        self.assertFalse(current())
        env["lifecycle_background"][0]=False
        env["dhan_feed"].connected=False
        self.assertFalse(current())
        self.assertIn("deepcopy(advanced),persist=False",source)
        self.assertIn("if done:return task.result() if owner() else None",source)
        self.assertIn("if restored or combined_age<0",source)

    def test_r1_capacity_and_visible_worker_ownership_contract(self):
        import ast
        from pathlib import Path
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        funcs={n.name:ast.get_source_segment(source,n) for n in ast.walk(ast.parse(source))
               if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        doctor=funcs["run_cached_test"]
        self.assertLess(doctor.index("count=len(chosen)"),doctor.index("str(count)"))
        self.assertLess(doctor.index("try:"),doctor.index("str(count)"))
        self.assertIn("await local_analysis_pool.run(benchmark_cached_capacity",doctor)
        self.assertIn("await local_analysis_pool.run(diagnostic_analyze",doctor)
        self.assertIn("if not input_current():return",doctor)
        self.assertLess(doctor.rindex("if not input_current():return"),doctor.index("stock_diagnostic_registry.reconcile"))
        self.assertIn("busy[0]=False",doctor)
        self.assertIn("with news_lock:",doctor)
        self.assertIn("visible[offset:offset+local_analysis_pool.workers]",funcs["watch_visible_tick"])
        self.assertIn("if not tick_owner_current():continue",funcs["watch_visible_tick"])
        self.assertIn("if not shared_symbol_current(sym):continue",funcs["refresh_shared_analysis"])
        self.assertIn("if updated and shared_owner_current():",funcs["refresh_shared_analysis"])
        self.assertIn("lifecycle_background[0]",funcs["flush_view_refresh"])
