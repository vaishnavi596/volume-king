"""The first market-data refresh must not be blocked by a zero uptime clock.

These tests execute actual nested app callbacks with local asynchronous fakes.
No Dhan/Oracle network, orders, device actions, or long-running schedulers.
"""
import ast
import asyncio
import sys
import textwrap
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
TREE=ast.parse(SOURCE)

def function_source(name):
    items=[node for node in ast.walk(TREE)
           if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))
           and node.name==name]
    if len(items)!=1:
        raise AssertionError("Expected one callback: "+name)
    return textwrap.dedent(ast.get_source_segment(SOURCE,items[0]))

def compile_callback(name,scope):
    exec(compile(function_source(name),str(ROOT/"src"/"main.py"),"exec"),scope)
    return scope[name]

class FinishedOneTick(Exception):
    pass

class ColdBootRefreshSentinelTests(unittest.TestCase):
    def test_first_manual_dhan_quote_refresh_allowed_at_monotonic_ten_seconds(self):
        called=[]
        async def equity():
            called.append("equity")
        async def index(force=False):
            called.append(("index",force))
        scope={"prefs":{"source":"Dhan"},
               "dhan_feed":SimpleNamespace(connected=True,cooldown_remaining=lambda _:0),
               "watch_batch_busy":[False],"index_refresh_busy":[False],
               "manual_quote_last_attempt":[0.0],
               "time":SimpleNamespace(monotonic=lambda:10.0),
               "watch_batch_status":[""],
               "request_view_refresh":lambda tab:called.append(("repaint",tab)),
               "refresh_watch_batch":equity,"refresh_dhan_index_quotes":index,
               "refresh_hours":lambda:True,"current":[4]}
        fn=compile_callback("refresh_all_dhan_quotes",scope)
        asyncio.run(fn())
        self.assertEqual(called,["equity",("index",True)])
        self.assertEqual(scope["manual_quote_last_attempt"][0],10.0)
        asyncio.run(fn())
        self.assertEqual(called,["equity",("index",True),("repaint",4)])
        self.assertIn("Manual refresh available",scope["watch_batch_status"][0])

    def test_first_manual_quote_respects_real_provider_cooldown(self):
        called=[]
        scope={"prefs":{"source":"Dhan"},
            "dhan_feed":SimpleNamespace(connected=True,cooldown_remaining=lambda _:25),
            "watch_batch_busy":[False],"index_refresh_busy":[False],
            "manual_quote_last_attempt":[0.0],
            "time":SimpleNamespace(monotonic=lambda:10.0),
            "watch_batch_status":[""],
            "request_view_refresh":lambda tab:called.append(("repaint",tab)),
            "refresh_watch_batch":lambda:None,
            "refresh_dhan_index_quotes":lambda *args:None}
        asyncio.run(compile_callback("refresh_all_dhan_quotes",scope)())
        self.assertEqual(scope["manual_quote_last_attempt"][0],0.0)
        self.assertIn("cooling down",scope["watch_batch_status"][0])
        self.assertEqual(called,[("repaint",4)])

    def test_after_hours_manual_quote_then_one_historical_refresh_no_51_fanout(self):
        calls=[]
        async def equity():
            calls.append("equity")
        async def index(force=False):
            calls.append(("index",force))
        async def one_history(gen,*,explicit_closed=False):
            calls.append(("1m-history",gen,explicit_closed))
            return True
        scope={"prefs":{"source":"Dhan"},
            "dhan_feed":SimpleNamespace(connected=True,cooldown_remaining=lambda _:0),
            "watch_batch_busy":[False],"index_refresh_busy":[False],
            "manual_quote_last_attempt":[0.0],
            "time":SimpleNamespace(monotonic=lambda:10.0),
            "watch_batch_status":["Dhan last known prices checked"],
            "request_view_refresh":lambda tab:calls.append(("repaint",tab)),
            "refresh_watch_batch":equity,"refresh_dhan_index_quotes":index,
            "refresh_hours":lambda:False,"current":[4],
            "dhan_history_scan_active":[False],"provider_generation":[3],
            "warm_selected_watch_three_minute_early":one_history}
        fn=compile_callback("refresh_all_dhan_quotes",scope)
        asyncio.run(fn())
        self.assertEqual(calls,["equity",("index",True),
                                ("1m-history",3,True),("repaint",4)])
        self.assertIn("HIST",scope["watch_batch_status"][0])
        asyncio.run(fn())  # Existing 30-second manual floor blocks repeat.
        self.assertEqual(calls[-1],("repaint",4))
        self.assertEqual([c for c in calls if isinstance(c,tuple)
                          and c[0]=="1m-history"],[("1m-history",3,True)])

    def test_closed_manual_candle_skips_busy_main_scan_after_quote(self):
        called=[]
        async def equity():
            called.append("equity")
        async def index(force=False):
            called.append("index")
        async def invalid_history(*args,**kwargs):
            raise AssertionError("must not run while 54-symbol 5m lane active")
        scope={"prefs":{"source":"Dhan"},
            "dhan_feed":SimpleNamespace(connected=True,cooldown_remaining=lambda _:0),
            "watch_batch_busy":[False],"index_refresh_busy":[False],
            "manual_quote_last_attempt":[0.0],
            "time":SimpleNamespace(monotonic=lambda:10.0),
            "watch_batch_status":["Quote pass"],
            "request_view_refresh":lambda _:None,
            "refresh_watch_batch":equity,"refresh_dhan_index_quotes":index,
            "refresh_hours":lambda:False,"current":[4],
            "dhan_history_scan_active":[True],"provider_generation":[3],
            "warm_selected_watch_three_minute_early":invalid_history}
        asyncio.run(compile_callback("refresh_all_dhan_quotes",scope)())
        self.assertEqual(called,["equity","index"])
        self.assertIn("main scan busy",scope["watch_batch_status"][0])

    def test_first_auto_option_refresh_allowed_at_monotonic_ten_seconds(self):
        called=[]
        last=[0.0]
        async def fetch():
            called.append("read-only option")
            last[0]=10.0
        async def tick(seconds):
            self.assertEqual(seconds,15)
            raise FinishedOneTick()
        scope={"app_active":[True],"current":[0],"refresh_hours":lambda:True,
            "prefs":{"source":"Dhan"},
            "dhan_feed":SimpleNamespace(connected=True,cooldown_remaining=lambda path:0),
            "chain_symbol":SimpleNamespace(value="NIFTY"),
            "DHAN_VERIFIED_SYMBOLS":{"NIFTY"},
            "option_feed_busy":[False],"dhan_option_last_attempt":last,
            "provider_generation":[0],
            "option_retry_until":{},
            "option_expiry_choice":SimpleNamespace(value="Nearest"),
            "expiry":SimpleNamespace(value=""),
            "time":SimpleNamespace(monotonic=lambda:10.0),
            "asyncio":SimpleNamespace(sleep=tick),
            "refresh_selected_options":fetch}
        fn=compile_callback("option_poll",scope)
        with self.assertRaises(FinishedOneTick):
            asyncio.run(fn())
        self.assertEqual(called,["read-only option"])
        with self.assertRaises(FinishedOneTick):
            asyncio.run(fn())
        self.assertEqual(called,["read-only option"])

    def test_oracle_assessment_requests_once_per_missing_symbol_key_at_ten_seconds(self):
        requested=[]
        cache={}
        attempts={}
        async def tick(seconds):
            if seconds==4:
                return
            self.assertEqual(seconds,15)
            raise FinishedOneTick()
        async def to_thread(fn,symbol,**kwargs):
            return fn(symbol,**kwargs)
        feed=SimpleNamespace(connected=True,
           assessment=lambda sym,**selectors:requested.append((sym,selectors)) or
               {"symbol":sym,"source":"dhan","freshness":"unverified"})
        scope={"app_active":[True],"lifecycle_background":[False],
            "prefs":{"source":"Dhan"},"dhan_feed":feed,
            "provider_generation":[0],
            "scan_symbol":SimpleNamespace(value="TCS"),
            "scan_tf":SimpleNamespace(value="3m"),
            "chain_symbol":SimpleNamespace(value="NIFTY"),
            "expiry":SimpleNamespace(value="2026-11-26"),
            "date":__import__("datetime").date,
            "bot_symbol":SimpleNamespace(value="TCS"),
            "DHAN_VERIFIED_SYMBOLS":{"NIFTY","TCS"},
            "oracle_assessment_attempts":attempts,
            "oracle_assessment_cache_generation":[0],
            "oracle_assessment_cache":cache,
            "current":[0],"time":SimpleNamespace(monotonic=lambda:10.0),
            "asyncio":SimpleNamespace(sleep=tick,to_thread=to_thread,
                                      CancelledError=asyncio.CancelledError),
            "request_view_refresh":lambda x:None,
            "log_error":lambda *args:None}
        compile_callback("oracle_assessment_context",scope)
        fn=compile_callback("oracle_assessment_poll",scope)
        with self.assertRaises(FinishedOneTick):
            asyncio.run(fn())
        expected=[
            ("TCS",{"timeframe":"3m","expiry":None}),
            ("NIFTY",{"timeframe":"1m","expiry":"2026-11-26"}),
        ]
        self.assertEqual(requested,expected)
        self.assertEqual(set(cache),{"TCS","NIFTY"})
        self.assertEqual(set(attempts),{
            (0,"TCS","3m",None),
            (0,"NIFTY","1m","2026-11-26"),
        })
        with self.assertRaises(FinishedOneTick):
            asyncio.run(fn())
        self.assertEqual(requested,expected)

    def test_assessment_ui_hides_old_selection_after_timeframe_or_expiry_change(self):
        selected_tf=SimpleNamespace(value="1m")
        selected_expiry=SimpleNamespace(value="2026-11-26")
        record={"fetched":10.0,"data":{"symbol":"NIFTY"},
                "timeframe":"1m","expiry":"2026-11-26"}
        context={"scan_symbol":SimpleNamespace(value="NIFTY"),
                 "scan_tf":selected_tf,
                 "chain_symbol":SimpleNamespace(value="NIFTY"),
                 "expiry":selected_expiry,
                 "date":__import__("datetime").date,
                 "provider_generation":[0],
                 "oracle_assessment_cache_generation":[0],
                 "oracle_assessment_cache":{"NIFTY":record},
                 "oracle_assessment_attempts":{},
                 "prefs":{"source":"Dhan"},
                 "dhan_feed":SimpleNamespace(connected=True),
                 "assessment_lines":lambda symbol,cache:["MATCHED"]}
        compile_callback("oracle_assessment_context",context)
        notes=compile_callback("oracle_assessment_notes",context)
        self.assertEqual(notes("NIFTY"),["MATCHED"])
        selected_tf.value="3m"
        self.assertIn("WAIT",notes("NIFTY")[0])
        selected_tf.value="1m"
        selected_expiry.value="2026-12-03"
        self.assertIn("WAIT",notes("NIFTY")[0])
        selected_expiry.value="2026-11-26"
        self.assertEqual(notes("NIFTY"),["MATCHED"])

    def test_auto_quote_navigation_resume_use_never_attempted_sentinel(self):
        source=function_source("dhan_quote_poll")
        self.assertIn('max(quote_auto_last_attempt[0],watch_batch_last_attempt[0])<=0',source)
        self.assertIn('time.monotonic()-max(quote_auto_last_attempt[0],watch_batch_last_attempt[0])>=60',source)
        nav=function_source("render_page")
        self.assertIn('watch_batch_last_attempt[0]<=0',nav)
        self.assertIn('time.monotonic()-watch_batch_last_attempt[0]>=60',nav)
        resume=function_source("refresh_after_resume")
        self.assertIn('max(quote_auto_last_attempt[0],watch_batch_last_attempt[0])<=0',resume)
        self.assertIn('time.monotonic()-max(quote_auto_last_attempt[0],watch_batch_last_attempt[0])>=60',resume)
        assessment=function_source("oracle_assessment_poll")
        self.assertIn('key in oracle_assessment_attempts',assessment)
        self.assertIn('now-oracle_assessment_attempts[key]<180',assessment)
        self.assertNotIn('oracle_assessment_attempts.get(key,0)',assessment)


if __name__=="__main__":
    unittest.main()
