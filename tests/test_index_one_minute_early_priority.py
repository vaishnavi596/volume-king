"""Source and executable offline tests for early 1m NIFTY/BANKNIFTY/SENSEX.

The initial 5m candle scan and 1m index history fetches use one serialized
provider lane. These tests use fake cached/history data; no Dhan requests.
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


def async_method_source(name):
    methods=[n for n in ast.walk(TREE) if isinstance(n,ast.AsyncFunctionDef)
             and n.name==name]
    if len(methods)!=1:
        raise AssertionError("Expected unique async function: "+name)
    return textwrap.dedent(ast.get_source_segment(SOURCE,methods[0]))


class EarlyIndexOneMinuteTests(unittest.TestCase):
    @staticmethod
    def fixture():
        calls=[]
        errors=[]
        rows=[[20000+i*60,100,105,98,102,1000] for i in range(35)]
        snapshots={}
        old_quotes={"NIFTY":{"source":"Dhan","bars":"unmodified 5m","price":25000}}
        previous={}
        session={"open":True,"cooldown":0}
        now=time.monotonic()
        feed=SimpleNamespace(connected=True,
            cooldown_remaining=lambda path:session["cooldown"])
        async def no_sleep(seconds):
            calls.append(("pace",seconds))
        async def fake_to_thread(fn,*args):
            calls.append(("history",args))
            return fn(*args)
        scope={
            "current":[0],"app_active":[True],"lifecycle_background":[False],
            "prefs":{"source":"Dhan"},"dhan_feed":feed,
            "provider_generation":[0],"refresh_hours":lambda:session["open"],
            "index_one_minute_busy":[False],
            "watch_three_minute_warm_busy":[False],
            "index_candle_generation":[None],
            "index_candle_last_attempt":[0.0],
            "time":time,"angel_feed":SimpleNamespace(epoch=0),
            "market_registry_lock":threading.RLock(),"market_recent":{},
            "shared_history":lambda sym,tf:previous.get((sym,tf),{}),
            "valid_candle_history":valid_candle_history,
            "retain_candle_history":retain_candle_history,
            "get_market_data":lambda sym,tf,duration:
                {"source":"Dhan","bars":[list(row) for row in rows],
                 "candle_fetched_at":time.time()},
            "chart_snapshots":snapshots,"quotes":old_quotes,
            "request_view_refresh":lambda tab:calls.append(("repaint",tab)),
            "log_error":lambda name,error:errors.append((name,type(error).__name__)),
            "remember_candle_failure":lambda *args:errors.append(tuple(args)),
            "asyncio":SimpleNamespace(sleep=no_sleep,to_thread=fake_to_thread,
                 wait_for=asyncio.wait_for,CancelledError=asyncio.CancelledError)
        }
        exec(compile(async_method_source("warm_index_one_minute_early"),
                     str(ROOT/"src"/"main.py"),"exec"),scope)
        return scope,calls,errors,rows,previous,session,now

    @staticmethod
    def invoke(scope,generation=0):
        return asyncio.run(scope["warm_index_one_minute_early"](generation))

    @staticmethod
    def histories(calls):
        return [row for row in calls if row[0]=="history"]

    def test_three_indices_published_before_equity_tail_in_serial_order(self):
        s,calls,errors,rows,previous,session,now=self.fixture()
        s["dhan_history_scan_active"]=[True]
        self.assertEqual(self.invoke(s),3)
        requested=[row[1] for row in self.histories(calls)]
        self.assertEqual(requested,[
            ("NIFTY","1m","2d"),("BANKNIFTY","1m","2d"),("SENSEX","1m","2d")])
        for name in ("NIFTY","BANKNIFTY","SENSEX"):
            q=s["chart_snapshots"][(name,"1m",0)]
            self.assertEqual(q["bars"],rows)
            self.assertTrue(q["historical"])
            self.assertFalse(q["live_verified"])
            self.assertEqual(q["freshness"],"historical_unverified")
            self.assertEqual(q["_scanner_timeframe"],"1m")
            self.assertNotIn((name,"5m",0),s["chart_snapshots"])
        self.assertEqual(s["quotes"]["NIFTY"]["bars"],"unmodified 5m")
        self.assertEqual(s["index_candle_generation"][0],0)
        self.assertGreater(s["index_candle_last_attempt"][0],0)
        self.assertFalse(s["index_one_minute_busy"][0])
        self.assertFalse(errors)

    def test_existing_180s_index_clock_prevents_duplicate_triplet(self):
        s,calls,_,_,_,_,_=self.fixture()
        self.assertEqual(self.invoke(s),3)
        self.assertEqual(self.invoke(s),0)
        self.assertEqual(len(self.histories(calls)),3)
        self.assertEqual(len([x for x in calls if x==("pace",1.5)]),3)

    def test_cached_index_history_does_not_incur_new_pacing(self):
        s,calls,_,_,_,_,now=self.fixture()
        for index_sym in ("NIFTY","BANKNIFTY","SENSEX"):
            key=(0,0,True,"Dhan",index_sym,"1m","2d")
            s["market_recent"][key]=(now,{"source":"Dhan"})
        self.assertEqual(self.invoke(s),3)
        self.assertEqual(len(self.histories(calls)),3)
        self.assertFalse(any(x==("pace",1.5) for x in calls))

    def test_recent_valid_one_minute_index_needs_no_second_request(self):
        s,calls,_,rows,prior,_,_=self.fixture()
        prior[("NIFTY","1m")]={"source":"Dhan","bars":rows,
                               "candle_fetched_at":time.time()-10}
        self.assertEqual(self.invoke(s),2)
        self.assertEqual([x[1][0] for x in self.histories(calls)],
                         ["BANKNIFTY","SENSEX"])

    def test_market_closed_disconnected_cooldown_or_foreground_mismatch_blocks(self):
        for reason in ("closed","disconnected","cooldown","background",
                       "generation","busy","watch_busy","not_visible"):
            with self.subTest(reason=reason):
                s,calls,_,_,_,session,_=self.fixture()
                if reason=="closed":session["open"]=False
                elif reason=="disconnected":s["dhan_feed"].connected=False
                elif reason=="cooldown":session["cooldown"]=30
                elif reason=="background":s["lifecycle_background"][0]=True
                elif reason=="generation":s["provider_generation"][0]=1
                elif reason=="busy":s["index_one_minute_busy"][0]=True
                elif reason=="watch_busy":s["watch_three_minute_warm_busy"][0]=True
                elif reason=="not_visible":s["current"][0]=2
                self.assertEqual(self.invoke(s),0)
                self.assertFalse(self.histories(calls))
                self.assertEqual(s["index_candle_generation"][0],None)

    def test_partial_history_keeps_only_same_provider_last_good_candles(self):
        s,calls,_,rows,prior,_,_=self.fixture()
        prior[("NIFTY","1m")]={"source":"Dhan","bars":rows,
            "candle_fetched_at":time.time()-500}
        def short(sym,tf,days):
            return {"source":"Dhan","bars":rows[-3:],"live_verified":True}
        s["get_market_data"]=short
        self.assertEqual(self.invoke(s),1)
        q=s["chart_snapshots"][("NIFTY","1m",0)]
        self.assertEqual(q["bars"],rows)
        self.assertTrue(q["historical"])
        self.assertFalse(q["live_verified"])
        self.assertNotIn(("NIFTY","5m",0),s["chart_snapshots"])

    def test_wrong_provider_does_not_create_index_signal(self):
        s,calls,_,_,_,_,_=self.fixture()
        s["get_market_data"]=lambda *args:{"source":"Yahoo Finance","bars":[]}
        self.assertEqual(self.invoke(s),0)
        # A malformed response for one index must not suppress the other two.
        self.assertEqual([entry[1][0] for entry in self.histories(calls)],
                         ["NIFTY","BANKNIFTY","SENSEX"])
        self.assertEqual(s["chart_snapshots"],{})
        self.assertFalse(s["index_one_minute_busy"][0])

    def test_rate_limit_after_first_attempt_cancels_remaining_indices(self):
        s,calls,errors,_,_,session,_=self.fixture()
        def hit_rate_limit(sym,tf,duration):
            session["cooldown"]=30
            raise RuntimeError("mocked provider 429")
        s["get_market_data"]=hit_rate_limit
        self.assertEqual(self.invoke(s),0)
        self.assertEqual(len(self.histories(calls)),1)
        self.assertTrue(any(row[0]=="early_index_1m_NIFTY" for row in errors))
        self.assertFalse(s["index_one_minute_busy"][0])
        self.assertEqual(s["index_candle_generation"][0],0)

    def test_source_reuses_index_clock_and_does_not_overlap_full_five_minute_tail(self):
        early=async_method_source("warm_index_one_minute_early")
        market=async_method_source("refresh_market")
        periodic=async_method_source("dhan_index_candle_poll")
        self.assertLess(market.index("await warm_index_one_minute_early(generation)"),
                        market.index("for sym in symbols[1:]:"))
        self.assertLess(market.index("await warm_selected_watch_three_minute_early(generation)"),
                        market.index("await warm_index_one_minute_early(generation)"))
        self.assertIn("index_candle_last_attempt[0]=now",early)
        self.assertIn("index_candle_generation[0]=generation",early)
        self.assertIn('dhan_feed.cooldown_remaining("/dhan/intraday")>0',early)
        self.assertIn("await asyncio.sleep(1.5)",early)
        self.assertIn('get_market_data,index_sym,"1m","2d"',early)
        self.assertNotIn("asyncio.gather(",early)
        self.assertNotIn('get_market_data,index_sym,"3m"',early)
        self.assertIn("time.monotonic()-index_candle_last_attempt[0]>=180",periodic)
        self.assertIn("not dhan_history_scan_active[0]",periodic)
        self.assertIn("index_one_minute_busy[0]=True",periodic)


if __name__=="__main__":
    unittest.main()
