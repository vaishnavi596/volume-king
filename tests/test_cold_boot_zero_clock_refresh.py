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
            "clone_v2_gateway":SimpleNamespace(connected=False),
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
            "clone_v2_gateway":SimpleNamespace(connected=False),
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
            "clone_v2_gateway":SimpleNamespace(connected=False),
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
            "clone_v2_gateway":SimpleNamespace(connected=False),
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
        repaints=[]
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
            "prefs":{"source":"Dhan","paper_positions":{"TCS":{"side":"BUY"}}},"dhan_feed":feed,
            "provider_generation":[0],
            "scan_symbol":SimpleNamespace(value="TCS"),
            "scan_tf":SimpleNamespace(value="3m"),
            "chain_symbol":SimpleNamespace(value="NIFTY"),
            "expiry":SimpleNamespace(value="2026-11-26"),
            "date":__import__("datetime").date,
            "bot_symbol":SimpleNamespace(value="TCS"),
            "DHAN_VERIFIED_SYMBOLS":{"NIFTY","BANKNIFTY","SENSEX","TCS"},
            "oracle_assessment_attempts":attempts,
            "oracle_assessment_cache_generation":[0],
            "oracle_assessment_closed_bootstrap_generation":[None],
            "refresh_hours":lambda:True,
            "oracle_assessment_cache":cache,
            "current":[0],"time":SimpleNamespace(monotonic=lambda:10.0),
            "asyncio":SimpleNamespace(sleep=tick,to_thread=to_thread,
                                      CancelledError=asyncio.CancelledError),
            "request_view_refresh":lambda x:repaints.append(x),
            "log_error":lambda *args:None}
        compile_callback("oracle_assessment_context",scope)
        fn=compile_callback("oracle_assessment_poll",scope)
        with self.assertRaises(FinishedOneTick):
            asyncio.run(fn())
        expected=[
            ("NIFTY",{"timeframe":"1m","expiry":None}),
            ("BANKNIFTY",{"timeframe":"1m","expiry":None}),
            ("SENSEX",{"timeframe":"1m","expiry":None}),
            ("TCS",{"timeframe":"3m","expiry":None}),
        ]
        self.assertEqual(requested,expected)
        # Three visible indices plus independent paper position, one repaint.
        self.assertEqual(repaints,[0])
        self.assertEqual(set(cache),{
            (0,"NIFTY","1m",None),
            (0,"BANKNIFTY","1m",None),
            (0,"SENSEX","1m",None),
            (0,"TCS","3m",None),
        })
        self.assertEqual(set(attempts),set(cache))
        with self.assertRaises(FinishedOneTick):
            asyncio.run(fn())
        self.assertEqual(requested,expected)
        self.assertEqual(repaints,[0])

    def test_watchlist_poll_rotates_one_visible_3m_context_per_cycle(self):
        requested=[]
        async def tick(seconds):
            if seconds!=4:
                raise FinishedOneTick()
        async def to_thread(fn,sym,**kwargs):
            return fn(sym,**kwargs)
        feed=SimpleNamespace(connected=True,assessment=lambda sym,**selectors:
            requested.append((sym,selectors["timeframe"],selectors["expiry"])) or
            {"symbol":sym,"signal_eligible":False,"live_orders_enabled":False})
        scope={"app_active":[True],"lifecycle_background":[False],
               "prefs":{"source":"Dhan"},"dhan_feed":feed,
               "provider_generation":[0],
               "scan_symbol":SimpleNamespace(value="NIFTY"),
               "scan_tf":SimpleNamespace(value="1m"),
               "chain_symbol":SimpleNamespace(value="NIFTY"),
               "expiry":SimpleNamespace(value="2026-11-26"),
               "date":__import__("datetime").date,
               "bot_symbol":SimpleNamespace(value="NIFTY"),
               "DHAN_VERIFIED_SYMBOLS":{"NIFTY","BANKNIFTY","SENSEX",
                                        "TCS","INFY","SBIN"},
               "watch_groups":[["TCS","INFY","SBIN"]],
               "active_watch":[0],
               "search":SimpleNamespace(value="INF"),
               "oracle_assessment_attempts":{},
               "oracle_assessment_cache_generation":[0],
               "oracle_assessment_closed_bootstrap_generation":[None],
               "oracle_assessment_watch_cursor":[0],
               "refresh_hours":lambda:True,
               "oracle_assessment_cache":{},
               "current":[4],"time":SimpleNamespace(monotonic=lambda:10.0),
               "asyncio":SimpleNamespace(sleep=tick,to_thread=to_thread,
                                         CancelledError=asyncio.CancelledError),
               "request_view_refresh":lambda tab:None,
               "log_error":lambda *args:None}
        compile_callback("oracle_assessment_context",scope)
        fn=compile_callback("oracle_assessment_poll",scope)
        with self.assertRaises(FinishedOneTick):
            asyncio.run(fn())
        self.assertIn(("INFY","3m",None),requested)
        self.assertNotIn(("TCS","3m",None),requested)
        self.assertEqual(sum(sym in ("TCS","INFY") for sym,tf,exp in requested),1)
        self.assertIn((0,"INFY","3m",None),scope["oracle_assessment_cache"])
        # A changed Watchlist search selects another key even inside 180s;
        # unchanged index contexts must remain on the existing attempt budget.
        scope["search"].value="TCS"
        with self.assertRaises(FinishedOneTick):
            asyncio.run(fn())
        self.assertIn(("TCS","3m",None),requested)
        self.assertEqual(sum(sym in ("TCS","INFY") for sym,tf,exp in requested),2)
        self.assertEqual(len(requested),2)
        scope["search"].value=""
        with self.assertRaises(FinishedOneTick):
            asyncio.run(fn())
        self.assertIn(("SBIN","3m",None),requested)
        self.assertEqual(len(requested),3)
        self.assertEqual(sum(sym in ("TCS","INFY","SBIN") for sym,tf,exp in requested),3)

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
                 "oracle_assessment_cache":{(0,"NIFTY","1m","2026-11-26"):record},
                 "oracle_assessment_attempts":{},
                 "prefs":{"source":"Dhan"},
                 "dhan_feed":SimpleNamespace(connected=True),
                 "assessment_lines":lambda symbol,cache:["MATCHED"]}
        compile_callback("oracle_assessment_context",context)
        notes=compile_callback("oracle_assessment_notes",context)
        self.assertEqual(notes("NIFTY","options"),["MATCHED"])
        self.assertIn("WAIT",notes("NIFTY","scanner")[0])
        selected_tf.value="3m"
        self.assertIn("WAIT",notes("NIFTY","scanner")[0])
        selected_tf.value="1m"
        selected_expiry.value="2026-12-03"
        self.assertIn("WAIT",notes("NIFTY","options")[0])
        selected_expiry.value="2026-11-26"
        self.assertEqual(notes("NIFTY","options"),["MATCHED"])


    def test_unsupported_scanner_interval_never_borrows_index_1m_evidence(self):
        tf=SimpleNamespace(value="15m")
        scope={"scan_symbol":SimpleNamespace(value="NIFTY"),
               "scan_tf":tf,
               "chain_symbol":SimpleNamespace(value="NIFTY"),
               "expiry":SimpleNamespace(value="2026-11-26"),
               "date":__import__("datetime").date,
               "provider_generation":[0],
               "oracle_assessment_cache_generation":[0],
               "oracle_assessment_cache":{
                   (0,"NIFTY","1m",None):{
                       "fetched":100,"timeframe":"1m","expiry":None,
                       "data":{"symbol":"NIFTY"}}},
               "oracle_assessment_attempts":{},
               "prefs":{"source":"Dhan"},
               "dhan_feed":SimpleNamespace(connected=True),
               "assessment_lines":lambda symbol,cached:["WRONG 1M BORROW"]}
        compile_callback("oracle_assessment_context",scope)
        notes=compile_callback("oracle_assessment_notes",scope)
        for interval in ("15m","30m","1h","1d"):
            with self.subTest(interval=interval):
                tf.value=interval
                self.assertEqual(scope["oracle_assessment_context"]("NIFTY","scanner")[0],
                                 None)
                result=notes("NIFTY","scanner")
                self.assertIn("WAIT",result[0])
                self.assertNotIn("WRONG 1M BORROW",result)
        self.assertEqual(notes("NIFTY","overview"),["WRONG 1M BORROW"])
        tf.value="5m"
        self.assertEqual(scope["oracle_assessment_context"]("NIFTY","scanner")[0],
                         "5m")

    def test_same_index_scanner_5m_and_dashboard_1m_never_cross_label(self):
        selected_tf=SimpleNamespace(value="5m")
        selected_expiry=SimpleNamespace(value="2026-11-26")
        cache={}
        def put(tf,expiry_value):
            cache[(0,"NIFTY",tf,expiry_value)]={
                "fetched":10.0,"data":{"symbol":"NIFTY","timeframe":tf},
                "timeframe":tf,"expiry":expiry_value}
        put("5m",None)
        put("1m",None)
        put("1m","2026-11-26")
        scope={"scan_symbol":SimpleNamespace(value="NIFTY"),
               "scan_tf":selected_tf,
               "chain_symbol":SimpleNamespace(value="NIFTY"),
               "expiry":selected_expiry,
               "date":__import__("datetime").date,
               "provider_generation":[0],
               "oracle_assessment_cache_generation":[0],
               "oracle_assessment_cache":cache,
               "oracle_assessment_attempts":{},
               "prefs":{"source":"Dhan"},
               "dhan_feed":SimpleNamespace(connected=True),
               "assessment_lines":lambda symbol,view: [
                   view[symbol]["data"]["timeframe"]]}
        compile_callback("oracle_assessment_context",scope)
        notes=compile_callback("oracle_assessment_notes",scope)
        self.assertEqual(notes("NIFTY","scanner"),["5m"])
        self.assertEqual(notes("NIFTY","overview"),["1m"])
        self.assertEqual(notes("NIFTY","options"),["1m"])
        selected_tf.value="3m"
        self.assertIn("WAIT",notes("NIFTY","scanner")[0])
        self.assertEqual(notes("NIFTY","overview"),["1m"])
        selected_expiry.value="2026-12-03"
        self.assertIn("WAIT",notes("NIFTY","options")[0])
        self.assertEqual(notes("NIFTY","overview"),["1m"])
        scope["provider_generation"][0]=1
        self.assertIn("WAIT",notes("NIFTY","overview")[0])
        self.assertEqual(cache,{})

    def test_poller_maintains_overlapping_same_symbol_contexts_with_one_key_each(self):
        requested=[]
        cache={}
        attempts={}
        async def tick(seconds):
            if seconds!=4:
                raise FinishedOneTick()
        async def to_thread(fn,symbol,**kwargs):
            return fn(symbol,**kwargs)
        feed=SimpleNamespace(connected=True,assessment=lambda sym,**selectors:
            requested.append((sym,selectors["timeframe"],selectors["expiry"])) or
            {"symbol":sym,"live_orders_enabled":False,"signal_eligible":False})
        scope={"app_active":[True],"lifecycle_background":[False],
               "prefs":{"source":"Dhan"},"dhan_feed":feed,
               "provider_generation":[0],
               "scan_symbol":SimpleNamespace(value="NIFTY"),
               "scan_tf":SimpleNamespace(value="5m"),
               "chain_symbol":SimpleNamespace(value="NIFTY"),
               "expiry":SimpleNamespace(value="2026-11-26"),
               "date":__import__("datetime").date,
               "bot_symbol":SimpleNamespace(value="NIFTY"),
               "DHAN_VERIFIED_SYMBOLS":{"NIFTY","BANKNIFTY","SENSEX"},
               "oracle_assessment_attempts":attempts,
               "oracle_assessment_cache_generation":[0],
               "oracle_assessment_closed_bootstrap_generation":[None],
               "refresh_hours":lambda:True,
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
        self.assertEqual(requested,[
            ("NIFTY","1m",None),
            ("BANKNIFTY","1m",None),
            ("SENSEX","1m",None)])
        self.assertEqual(set(cache),set(attempts))
        with self.assertRaises(FinishedOneTick):
            asyncio.run(fn())
        self.assertEqual(len(requested),3)
        # Switching to Scanner uses its independent 5m cache and does not
        # refetch Dashboard's three index assessments.
        scope["current"][0]=3
        with self.assertRaises(FinishedOneTick):
            asyncio.run(fn())
        self.assertEqual(requested[-1],("NIFTY","5m",None))
        self.assertEqual(len(requested),4)
        scope["scan_tf"].value="3m"
        with self.assertRaises(FinishedOneTick):
            asyncio.run(fn())
        self.assertEqual(requested[-1],("NIFTY","3m",None))
        self.assertEqual(len(requested),5)
        for tf in ("1m","3m","5m"):
            self.assertIn((0,"NIFTY",tf,None),cache)
        # Options only requests the selected expiry while that page is active.
        scope["current"][0]=1
        with self.assertRaises(FinishedOneTick):
            asyncio.run(fn())
        self.assertEqual(requested[-1],("NIFTY","1m","2026-11-26"))
        self.assertEqual(len(requested),6)
        self.assertEqual(set(cache),set(attempts))
        with self.assertRaises(FinishedOneTick):
            asyncio.run(fn())
        self.assertEqual(len(requested),6)

    def test_auto_quote_navigation_resume_use_never_attempted_sentinel(self):
        source=function_source("dhan_quote_poll")
        self.assertIn("poll_due=auto_equity_quote_due(",source)
        self.assertIn("max(quote_auto_last_attempt[0],watch_batch_last_attempt[0])",source)
        from clone_smart_refresh_priority import auto_equity_quote_due
        self.assertTrue(auto_equity_quote_due(100.0,0.0))
        self.assertFalse(auto_equity_quote_due(159.0,100.0))
        self.assertTrue(auto_equity_quote_due(160.0,100.0))
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
