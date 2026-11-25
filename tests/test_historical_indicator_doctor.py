"""Cache-only Doctor observation of actual historical indicator execution."""
import unittest
from v3_smart_active_doctor import active_report

class HistoricalIndicatorDoctorTests(unittest.TestCase):
    def report(self, observed):
        return active_report(generation=1,symbols=[],quote_present=[],index_present=[],
            connected={},signal_present=[],attempts={},now_monotonic=1,market_open=False,
            errors=[],progress={},performance={},quote_attempt_age=None,
            historical_indicator_observation=observed)

    def row(self, observed):
        return next((r for r in self.report(observed)["active"]
                     if r["check"]=="HISTORICAL_INDICATOR_RUNTIME"),None)

    def test_unobserved_and_wrong_generation(self):
        for observed in ({},{"generation":2,"successes":1}):
            self.assertEqual(self.row(observed)["status"],"UNVERIFIED")

    def test_failure_is_actionable(self):
        row=self.row({"generation":1,"successes":1,"last_error":"ValueError"})
        self.assertEqual((row["status"],row["code"]),("ERROR","BK-HIST-001"))
        self.assertEqual(row["evidence"]["last_error"],"ValueError")

    def test_observed_success_hidden(self):
        self.assertIsNone(self.row({"generation":1,"successes":1,"last_error":None}))
        self.assertEqual(self.report({"generation":1,"successes":1})["provider_requests"],0)

    def test_index_worker_error_and_unverified_are_distinct(self):
        args=dict(generation=1,symbols=[],quote_present=[],index_present=[],
            connected={},signal_present=[],attempts={},now_monotonic=1,market_open=False,
            errors=[],progress={},performance={},quote_attempt_age=None)
        def row(value):
            return next((r for r in active_report(**args,historical_prewarm_observation=value)["active"]
                if r["check"]=="HISTORICAL_INDEX_WORKER"),None)
        self.assertEqual(row({"generation":2,"successes":1})["status"],"UNVERIFIED")
        self.assertEqual(row({"generation":1,"last_error":"ValueError"})["code"],"BK-HIST-WORKER-001")
        self.assertIsNone(row({"generation":1,"successes":1}))

    def test_index_worker_runs_before_publication_and_rechecks_generation(self):
        from pathlib import Path
        s=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text()
        worker=s.split("async def prewarm_index_historical_indicator(",1)[1].split("def historical_vote_agreement(",1)[0]
        self.assertIn("await local_analysis_pool.run(compute)",worker)
        self.assertIn("generation!=provider_generation[0]",worker)
        self.assertIn("historical_indicator_cache[identity]=result",worker)
        self.assertNotIn("get_market_data(",worker)
        poll=s.split("async def dhan_index_candle_poll():",1)[1].split("async def watch_three_minute_warmup():",1)[0]
        self.assertLess(poll.index("await prewarm_index_historical_indicator"),poll.index('chart_snapshots[(index_sym,"1m",generation)]=index_history'))

    def test_equity_worker_is_wired_and_bounded(self):
        from pathlib import Path
        s=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text()
        body=s.split("async def prewarm_equity_historical_indicator(",1)[1].split("def historical_vote_agreement(",1)[0]
        self.assertIn('tf not in ("3m","5m")',body)
        self.assertIn("await local_analysis_pool.run(compute)",body)
        self.assertIn("generation!=provider_generation[0]",body)
        self.assertIn("len(historical_equity_worker_inflight)>=local_analysis_pool.workers",body)
        self.assertNotIn("get_market_data(",body)
        self.assertIn('await prewarm_equity_historical_indicator(sym,shared_history(sym,"3m"),"3m",identity[0])',s)
        self.assertIn('await prewarm_equity_historical_indicator(sym,snapshot,"5m",generation)',s)

    def test_equity_worker_error_code(self):
        r=active_report(generation=1,symbols=[],quote_present=[],index_present=[],
            connected={},signal_present=[],attempts={},now_monotonic=1,market_open=False,
            errors=[],progress={},performance={},quote_attempt_age=None,
            historical_equity_worker_observation={"generation":1,"last_error":"ValueError"})
        self.assertEqual(next(x for x in r["active"] if x["check"]=="HISTORICAL_EQUITY_WORKER")["code"],"BK-HIST-WORKER-003")


    def test_equity_worker_real_function_cache_reuse_and_generation_guard(self):
        import ast
        import asyncio
        import math
        import textwrap
        import time
        from pathlib import Path
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text()
        node=next(n for n in ast.walk(ast.parse(source))
                  if isinstance(n,ast.AsyncFunctionDef) and n.name=="prewarm_equity_historical_indicator")
        calls=[]
        class Pool:
            workers=2
            async def run(self, fn):
                return fn()
        generation=[1]
        cache={}
        scope=dict(asyncio=asyncio,math=math,time=time,provider_generation=generation,
                   prefs={"source":"Dhan"},app_active=[True],lifecycle_background=[False],
                   filter_selected=["RSI"],filter_modes={"RSI":"Analysis"},
                   timeframe_spec=lambda tf:{"seconds":int(tf[:-1])*60},
                   historical_regular_session_bars=lambda bars,tf:bars,
                   quality_check=lambda bars,seconds,now:{"usable":True,"bars":bars},
                   analyze=lambda bars,selected,tf:(calls.append(tf) or {"bias":"BEARISH"}),
                   historical_indicator_cache=cache,historical_equity_worker_profile={},
                   historical_equity_worker_inflight=set(),historical_equity_worker_revision={},
                   local_analysis_pool=Pool(),log_error=lambda *args:self.fail(str(args)))
        exec(compile(textwrap.dedent(ast.get_source_segment(source,node)),"worker","exec"),scope)
        worker=scope["prewarm_equity_historical_indicator"]
        data={"source":"Dhan","_scanner_timeframe":"3m","bars":[(time.time()-900,100,101,99,100,10)]}
        async def check():
            self.assertTrue(await worker("RELIANCE",data,"3m",1))
            self.assertTrue(await worker("RELIANCE",data,"3m",1))
            self.assertEqual(calls,["3m"])
            self.assertEqual(len(cache),1)
            self.assertFalse(await worker("RELIANCE",data,"3m",2))
            self.assertFalse(await worker("RELIANCE",data,"5m",1))
            scope["lifecycle_background"][0]=True
            self.assertFalse(await worker("RELIANCE",data,"3m",1))
            self.assertFalse(scope["historical_equity_worker_inflight"])
        asyncio.run(check())
