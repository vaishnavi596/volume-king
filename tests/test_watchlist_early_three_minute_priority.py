"""Executable offline test for first-visible 3m Watchlist source priority.

The 5m full 51-equity scan stays serialized; a single selected 1m input may
borrow the existing Watchlist budget before the equity history tail.
No Dhan/Oracle connectivity, orders or long sleeps in this test.
"""
import ast
import asyncio
import sys
import textwrap
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from candle_retention import retain_candle_history, valid_candle_history

SOURCE=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
TREE=ast.parse(SOURCE)


def method_source(name):
    nodes=[n for n in ast.walk(TREE) if isinstance(n,ast.AsyncFunctionDef)
           and n.name==name]
    if len(nodes)!=1:
        raise AssertionError("Expected exactly one async function: "+name)
    return textwrap.dedent(ast.get_source_segment(SOURCE,nodes[0]))


class EarlyThreeMinutePriorityTests(unittest.TestCase):
    @staticmethod
    def fixture():
        calls=[]
        errors=[]
        charts={}
        window={"open":True}
        now=time.monotonic()
        cache={}
        last_provider=[0.0]
        attempts={}
        times=[]
        rows=[[10000+i*60,100,104,99,102,200] for i in range(35)]
        prior={}
        feed=SimpleNamespace(connected=True,cooldown_remaining=lambda path:0)
        async def fast_sleep(delay):
            calls.append(("spacing",delay))
        async def fake_to_thread(func,*args):
            calls.append(("request",args))
            return func(*args)
        def mock_history(sym,tf,days):
            return {"source":"Dhan","bars":[list(row) for row in rows],
                    "candle_fetched_at":time.time()}
        scope={
            "current":[4],"app_active":[True],"lifecycle_background":[False],
            "prefs":{"source":"Dhan"},"dhan_feed":feed,
            "clone_v2_gateway":SimpleNamespace(connected=True),
            "provider_generation":[0],"refresh_hours":lambda:window["open"],
            "watch_three_minute_warm_busy":[False],
            "watch_three_minute_upstream_times":times,
            "watch_three_minute_warm_attempts":attempts,
            "watch_three_minute_warm_last_provider":last_provider,
            "index_one_minute_busy":[False],
            "dhan_history_scan_active":[False],
            "watch_groups":[["TCS","INFY"],[],[],[],[]],"active_watch":[0],
            "search":SimpleNamespace(value=""),
            "DHAN_VERIFIED_SYMBOLS":{"TCS","INFY","NIFTY"},
            "shared_history":lambda sym,tf:prior.get((sym,tf),{}),
            "valid_candle_history":valid_candle_history,
            "angel_feed":SimpleNamespace(epoch=0),
            "market_registry_lock":threading.RLock(),
            "market_recent":cache,"time":time,
            "get_market_data":mock_history,
            "retain_candle_history":retain_candle_history,
            "chart_snapshots":charts,
            "request_view_refresh":lambda tab:calls.append(("repaint",tab)),
            "log_error":lambda where,e:errors.append((where,type(e).__name__)),
            "remember_candle_failure":lambda *args:errors.append(tuple(args)),
            "asyncio":SimpleNamespace(
                sleep=fast_sleep,to_thread=fake_to_thread,
                wait_for=asyncio.wait_for,CancelledError=asyncio.CancelledError)
        }
        priority=next(n for n in ast.walk(TREE)
                      if isinstance(n,ast.FunctionDef) and n.name=="watch_refresh_priority")
        exec(compile(textwrap.dedent(ast.get_source_segment(SOURCE,priority)),
                     str(ROOT/"src"/"main.py"),"exec"),scope)
        exec(compile(method_source("warm_selected_watch_three_minute_early"),
                     str(ROOT/"src"/"main.py"),"exec"),scope)
        return scope,calls,errors,window,rows,prior,now

    @staticmethod
    def invoke(scope):
        return asyncio.run(scope["warm_selected_watch_three_minute_early"](0))

    @staticmethod
    def requests(calls):
        return [x for x in calls if x[0]=="request"]

    def test_first_visible_one_minute_loaded_during_active_five_minute_scan(self):
        s,calls,errors,window,rows,prior,now=self.fixture()
        s["dhan_history_scan_active"]=[True] # Allowed only from serialized scan checkpoint.
        self.assertTrue(self.invoke(s))
        self.assertEqual(len(self.requests(calls)),1)
        self.assertEqual(self.requests(calls)[0][1],("TCS","1m","2d"))
        self.assertIn((0,"TCS"),s["watch_three_minute_warm_attempts"])
        self.assertEqual(len(s["watch_three_minute_upstream_times"]),1)
        snapshot=s["chart_snapshots"][("TCS","1m",0)]
        self.assertEqual(snapshot["bars"],rows)
        self.assertEqual(snapshot["_scanner_timeframe"],"1m")
        self.assertTrue(snapshot["historical"])
        self.assertFalse(snapshot["live_verified"])
        self.assertEqual(snapshot["freshness"],"historical_unverified")
        self.assertNotIn(("TCS","5m",0),s["chart_snapshots"])
        self.assertIn(("repaint",4),calls)
        self.assertFalse(s["watch_three_minute_warm_busy"][0])
        self.assertFalse(errors)

    def test_prior_attempt_cannot_repeat_same_symbol_in_same_budget_window(self):
        s,calls,_,_,_,_,_=self.fixture()
        s["watch_groups"][0]=["TCS"]
        self.assertTrue(self.invoke(s))
        self.assertFalse(self.invoke(s))
        self.assertEqual(len(self.requests(calls)),1)
        self.assertEqual(len(s["watch_three_minute_upstream_times"]),1)

    def test_cold_boot_monotonic_under_30s_allows_first_request_not_second(self):
        s,calls,errors,window,rows,prior,now=self.fixture()
        # GitHub's fast scoped runner reproduced an erroneous first-request
        # throttle: 0 means NEVER attempted, not a real monotonic timestamp.
        s["watch_groups"][0]=["TCS"]
        s["time"]=SimpleNamespace(monotonic=lambda:10.0,time=time.time)
        self.assertTrue(self.invoke(s))
        self.assertEqual(len(self.requests(calls)),1)
        self.assertEqual(s["watch_three_minute_warm_attempts"][(0,"TCS")],10.0)
        self.assertEqual(s["watch_three_minute_warm_last_provider"][0],10.0)
        self.assertFalse(self.invoke(s))
        self.assertEqual(len(self.requests(calls)),1)
        self.assertFalse(errors)

    def test_real_recent_attempt_and_provider_gap_still_block_at_10s_boot(self):
        for reason in ("symbol_attempt","global_provider_gap"):
            with self.subTest(reason=reason):
                s,calls,_,_,_,_,_=self.fixture()
                s["watch_groups"][0]=["TCS"]
                s["time"]=SimpleNamespace(monotonic=lambda:10.0,time=time.time)
                if reason=="symbol_attempt":
                    s["watch_three_minute_warm_attempts"][(0,"TCS")]=5.0
                else:
                    s["watch_three_minute_warm_last_provider"][0]=5.0
                self.assertFalse(self.invoke(s))
                self.assertFalse(self.requests(calls))

    def test_periodic_and_early_warmups_both_handle_unset_clock_sentinels(self):
        helper=method_source("warm_selected_watch_three_minute_early")
        periodic=method_source("watch_three_minute_warmup")
        for source in (helper,periodic):
            self.assertIn("key in watch_three_minute_warm_attempts",source)
            self.assertIn("now-watch_three_minute_warm_attempts[key]<180",source)
            self.assertIn("watch_three_minute_warm_last_provider[0]>0",source)
            self.assertIn("now-watch_three_minute_warm_last_provider[0]<10",source)
            self.assertNotIn("watch_three_minute_warm_attempts.get(key,0)",source)

    def test_exact_rolling_budget_and_global_10_second_spacing(self):
        for budget in ("twelve_requests","recent_previous"):
            with self.subTest(budget=budget):
                s,calls,_,_,_,_,now=self.fixture()
                if budget=="twelve_requests":
                    s["watch_three_minute_upstream_times"][:]=[now-14*i for i in range(1,13)]
                else:
                    s["watch_three_minute_warm_last_provider"][0]=now-5
                self.assertFalse(self.invoke(s))
                self.assertEqual(self.requests(calls),[])
                self.assertEqual(s["chart_snapshots"],{})
        s,calls,_,_,_,_,now=self.fixture()
        s["watch_three_minute_upstream_times"][:]=[now-190,now-185,now-181]
        self.assertTrue(self.invoke(s))
        self.assertEqual(len(s["watch_three_minute_upstream_times"]),1)

    def test_prior_cached_one_minute_history_does_not_spend_upstream_budget(self):
        s,calls,_,_,_,_,now=self.fixture()
        key=(0,0,True,"Dhan","TCS","1m","2d")
        s["market_recent"][key]=(now,{"source":"Dhan"})
        s["watch_three_minute_upstream_times"][:]=[now-60,now-50,now-40]
        s["watch_three_minute_warm_last_provider"][0]=now-5
        self.assertTrue(self.invoke(s))
        self.assertEqual(len(self.requests(calls)),1) # Local get_market_data cache retrieval.
        self.assertEqual(len(s["watch_three_minute_upstream_times"]),3)
        self.assertNotIn(("spacing",1.5),calls)

    def test_closed_disconnected_cooldown_background_or_wrong_generation_never_fetch(self):
        for reason in ("closed","disconnected","cooldown","background","generation","index_busy","not_watchlist"):
            with self.subTest(reason=reason):
                s,calls,_,window,_,_,_=self.fixture()
                if reason=="closed":window["open"]=False
                elif reason=="disconnected":s["dhan_feed"].connected=False
                elif reason=="cooldown":s["dhan_feed"].cooldown_remaining=lambda _:30
                elif reason=="background":s["lifecycle_background"][0]=True
                elif reason=="generation":s["provider_generation"][0]=1
                elif reason=="index_busy":s["index_one_minute_busy"][0]=True
                elif reason=="not_watchlist":s["current"][0]=0
                self.assertFalse(self.invoke(s))
                self.assertFalse(self.requests(calls))
                self.assertFalse(s["watch_three_minute_warm_busy"][0])

    def test_after_hours_history_requires_explicit_manual_flag_and_is_historical(self):
        s,calls,errors,window,rows,prior,now=self.fixture()
        window["open"]=False
        self.assertFalse(self.invoke(s)) # Automatic early priority still closed.
        self.assertTrue(asyncio.run(s["warm_selected_watch_three_minute_early"](
            0,explicit_closed=True)))
        req=self.requests(calls)
        self.assertEqual(len(req),1)
        self.assertEqual(req[0][1],("TCS","1m","2d"))
        self.assertEqual(len(s["watch_three_minute_upstream_times"]),1)
        entry=s["chart_snapshots"][("TCS","1m",0)]
        self.assertEqual(entry["_scanner_timeframe"],"1m")
        self.assertEqual(entry["freshness"],"historical_unverified")
        self.assertTrue(entry["historical"])
        self.assertFalse(entry["live_verified"])
        self.assertFalse(errors)

    def test_explicit_after_hours_never_competes_with_main_scan_or_cooldown(self):
        for reason in ("main_scan","provider_cooldown","twelve_budget","ten_gap",
                       "wrong_provider","wrong_generation","background"):
            with self.subTest(reason=reason):
                s,calls,errors,window,rows,prior,now=self.fixture()
                window["open"]=False
                if reason=="main_scan":s["dhan_history_scan_active"][0]=True
                elif reason=="provider_cooldown":s["dhan_feed"].cooldown_remaining=lambda _:30
                elif reason=="twelve_budget":
                    s["watch_three_minute_upstream_times"][:]=[now-14*i for i in range(1,13)]
                elif reason=="ten_gap":
                    s["watch_three_minute_warm_last_provider"][0]=now-5
                elif reason=="wrong_provider":s["prefs"]["source"]="Yahoo Finance"
                elif reason=="wrong_generation":s["provider_generation"][0]=1
                elif reason=="background":s["lifecycle_background"][0]=True
                self.assertFalse(asyncio.run(s["warm_selected_watch_three_minute_early"](
                    0,explicit_closed=True)))
                self.assertEqual(self.requests(calls),[])
                self.assertFalse(s["watch_three_minute_warm_busy"][0])

    def test_explicit_manual_retains_last_candle_when_partial_response_after_close(self):
        s,calls,errors,window,rows,prior,now=self.fixture()
        window["open"]=False
        prior[("TCS","1m")]={"source":"Dhan","bars":rows,
                            "candle_fetched_at":time.time()-300}
        s["get_market_data"]=lambda *args:{"source":"Dhan","bars":rows[-3:],
                                            "live_verified":True}
        self.assertTrue(asyncio.run(s["warm_selected_watch_three_minute_early"](
            0,explicit_closed=True)))
        data=s["chart_snapshots"][("TCS","1m",0)]
        self.assertEqual(data["bars"],rows)
        self.assertTrue(data["historical"])
        self.assertFalse(data["live_verified"])
        self.assertEqual(data["freshness"],"historical_unverified")
        self.assertFalse(errors)

    def test_partial_new_series_keeps_previous_one_minute_history_not_fake_live(self):
        s,calls,_,_,rows,prior,_=self.fixture()
        prior[("TCS","1m")]={"source":"Dhan","bars":rows,
                            "candle_fetched_at":time.time()-150}
        def short(sym,tf,days):
            return {"source":"Dhan","bars":rows[-2:],"live_verified":True}
        s["get_market_data"]=short
        self.assertTrue(self.invoke(s))
        shown=s["chart_snapshots"][("TCS","1m",0)]
        self.assertEqual(shown["bars"],rows)
        self.assertFalse(shown["live_verified"])
        self.assertTrue(shown["historical"])
        self.assertFalse(s["watch_three_minute_warm_busy"][0])

    def test_cross_provider_response_not_published_and_busy_releases(self):
        s,calls,errors,_,_,_,_=self.fixture()
        s["get_market_data"]=lambda *args:{"source":"Yahoo Finance","bars":[]}
        self.assertFalse(self.invoke(s))
        self.assertEqual(s["chart_snapshots"],{})
        self.assertFalse(s["watch_three_minute_warm_busy"][0])
        self.assertEqual(len(self.requests(calls)),1)

    def test_backend_error_does_not_block_remaining_five_minute_scan(self):
        s,calls,errors,_,_,_,_=self.fixture()
        def failing(*args):
            raise RuntimeError("offline-test simulated 429")
        s["get_market_data"]=failing
        self.assertFalse(self.invoke(s))
        self.assertFalse(s["watch_three_minute_warm_busy"][0])
        self.assertEqual(len(self.requests(calls)),1)
        self.assertTrue(any(row[0]=="watch_three_minute_early" for row in errors))

    def test_serial_insertion_and_shared_scheduler_counters(self):
        scan=method_source("refresh_market")
        helper=method_source("warm_selected_watch_three_minute_early")
        self.assertLess(scan.index("await warm_selected_watch_three_minute_early(generation)"),
                        scan.index("for sym in symbols[1:]:"))
        self.assertIn('get_market_data,sym,"1m","2d"',helper)
        self.assertIn('await asyncio.sleep(1.5)',helper)
        self.assertNotIn('asyncio.gather(',helper)
        self.assertIn('len(watch_three_minute_upstream_times)>=12',helper)
        self.assertIn('watch_three_minute_upstream_times.append(attempt_time)',helper)
        self.assertIn('watch_three_minute_warm_last_provider[0]<10',helper)
        self.assertIn('watch_three_minute_warm_attempts[key]=time.monotonic()',helper)
        self.assertIn('(not refresh_hours() and not explicit_closed)',helper)
        self.assertNotIn('get_market_data,sym,"3m"',helper)
        regular=method_source("watch_three_minute_warmup")
        for token in ('watch_three_minute_upstream_times','watch_three_minute_warm_attempts',
                      'watch_three_minute_warm_last_provider','watch_three_minute_warm_busy'):
            self.assertIn(token,helper)
            self.assertIn(token,regular)


if __name__=="__main__":
    unittest.main()
