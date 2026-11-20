"""Scanner simulation-only controls may not spend extra Dhan candle requests.

Exercise actual trigger_scan() with simple UI stubs; validate scanner chart's
same-timeframe last-good history retention. Pure offline, no broker transport.
"""
import ast
import sys
import textwrap
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from candle_retention import retain_candle_history

SOURCE=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
TREE=ast.parse(SOURCE)

def function_source(name):
    fn=next(n for n in ast.walk(TREE) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
            and n.name==name)
    return textwrap.dedent(ast.get_source_segment(SOURCE,fn))


class ScannerSelectedSourceSafetyTests(unittest.TestCase):
    @staticmethod
    def create_context():
        actions=[]
        symbol=SimpleNamespace(value="RELIANCE")
        timeframe=SimpleNamespace(value="1m")
        period=SimpleNamespace(value="7d")
        budget=SimpleNamespace(value="Custom")
        minimum=SimpleNamespace(value="20",visible=False)
        maximum=SimpleNamespace(value="200",visible=False)
        expiry=SimpleNamespace(value="14")
        auto=SimpleNamespace(value=True)
        status=SimpleNamespace(value="")
        page=SimpleNamespace(update=lambda:actions.append("update"),
            run_task=lambda function,*args:actions.append(("run",function,*args)))
        market=lambda:None
        scope={"scan_symbol":symbol,"scan_tf":timeframe,"scan_period":period,
               "scan_budget":budget,"scan_min":minimum,"scan_max":maximum,
               "scan_expiry":expiry,"scan_auto":auto,"scan_status":status,
               "page":page,"current":[3],"prefs":{"source":"Dhan"},
               "scan_selection_context":[("RELIANCE","1m","7d")],
               "scan_generation":[0],"scan_result":SimpleNamespace(controls=[]),
               "scan_last_success":[2],"scan_last_candle":[5],
               "selected_report_identity":["old"],"scan_filter_ready":[True],
               "scan_shared":{},"scan_busy":[False],
               "watch_signal_cache":{},
               "request_view_refresh":lambda tab:actions.append(("view_refresh",tab)),
               "save":lambda:actions.append("save"),
               "card":lambda obj:obj,"note":lambda msg:msg,
               "select":lambda tab:actions.append(("select",tab)),
               "scan_market":market,"refresh_hours":lambda:True}
        exec(compile(function_source("trigger_scan"),str(ROOT/"src"/"main.py"),"exec"),scope)
        return scope,actions

    def test_simulation_fields_update_locally_without_a_market_task(self):
        for field in ("scan_budget","scan_min","scan_max","scan_expiry","scan_auto"):
            with self.subTest(field=field):
                ctx,actions=self.create_context()
                ctx["trigger_scan"](SimpleNamespace(control=ctx[field]))
                self.assertFalse(any(isinstance(a,tuple) and a[0]=="run" for a in actions))
                self.assertEqual(ctx["scan_generation"][0],0)
                self.assertEqual(ctx["scan_min"].visible,field=="scan_budget")
                self.assertIn("no Dhan candle request",ctx["scan_status"].value)

    def test_real_symbol_change_still_queues_selected_candle_history(self):
        ctx,actions=self.create_context()
        ctx["scan_symbol"].value="TCS"
        ctx["trigger_scan"](SimpleNamespace(control=ctx["scan_symbol"]))
        self.assertEqual(ctx["scan_generation"][0],1)
        self.assertIn(("run",ctx["scan_market"],True),actions)
        self.assertEqual(ctx["scan_shared"]["symbol"],"TCS")

    def test_closed_session_selection_is_cache_only_without_broker_fetch(self):
        ctx,actions=self.create_context()
        ctx["refresh_hours"]=lambda:False
        ctx["scan_symbol"].value="TCS"
        ctx["trigger_scan"](SimpleNamespace(control=ctx["scan_symbol"]))
        self.assertEqual(ctx["scan_generation"][0],1)
        self.assertIn(("run",ctx["scan_market"],False),actions)
        self.assertEqual(ctx["scan_shared"]["symbol"],"TCS")

    def test_off_hours_scanner_entry_hydrates_cache_without_network(self):
        # Entering the Scanner after-hours must not require Settings > Retry.
        # This is a cache-only task and cannot call the Dhan broker.
        nav=function_source("render_page")
        self.assertIn('if changed and i==3 and scan_live.value and not scan_busy[0]:',nav)
        self.assertIn('dhan_feed.connected and not refresh_hours()',nav)
        self.assertIn('page.run_task(scan_market,False)',nav)
        self.assertNotIn('page.run_task(scan_market,True)',nav)

    def test_scanner_oi_context_explains_connection_and_expiry(self):
        view=function_source("scanner_option_context")
        self.assertIn('Dhan session not connected',view)
        self.assertIn('differs from Options',view)
        self.assertIn('auto-refresh pauses after market hours',view)
        self.assertIn('use explicit Retry Data',view)

    def test_finnifty_options_refresh_without_dashboard_index_expansion(self):
        self.assertIn('DHAN_VERIFIED_OPTION_SYMBOLS = DHAN_VERIFIED_SYMBOLS | {"FINNIFTY"}',SOURCE)
        self.assertIn('chain_symbol.value=="FINNIFTY"',function_source("option_poll"))
        self.assertIn('if sym!="FINNIFTY":',function_source("refresh_selected_options"))
        self.assertIn("symbol not in DHAN_VERIFIED_OPTION_SYMBOLS",
                      function_source("scanner_option_context"))

    def test_run_scan_and_filter_controls_restored_visibly(self):
        controls=function_source("scanner_controls")
        self.assertIn('ft.ElevatedButton("Run Scan"',controls)
        self.assertIn('on_click=run_scan',controls)
        self.assertIn('ft.OutlinedButton("Filters • Settings"',controls)
        self.assertIn('on_click=open_filter_settings',controls)
        self.assertIn('ft.Row([scan_live,scan_refresh]',controls)

    def test_auto_refresh_toggle_and_interval_are_visible_in_scanner(self):
        controls=function_source("scanner_controls")
        self.assertIn("ft.Row([scan_live,scan_refresh]",controls)
        self.assertIn("saved candles only",controls)
        self.assertIn('Auto Scan runs only while Scanner is visible',controls)
        # No unbounded background provider worker is authorized by controls.
        loop=function_source("auto_scan_loop")
        self.assertIn("while scan_live.value and generation==scan_auto_generation[0]",loop)
        self.assertIn("if current[0]!=3:",loop)
        self.assertIn("if not refresh_hours():",loop)

    def test_one_minute_default_preserves_saved_timeframe(self):
        self.assertIn('saved_scanner_tf=prefs.get("scanner_timeframe","1m")',SOURCE)
        self.assertIn('        saved_scanner_tf="1m"',SOURCE)
        self.assertIn('prefs["scanner_timeframe"]=scan_tf.value or "1m"',SOURCE)
        # Existing saved 3m/5m/15m/1h still takes precedence over default.
        setup=SOURCE.split('saved_scanner_tf=prefs.get("scanner_timeframe","1m")',1)[1].split(
            "    scan_expiry=",1)[0]
        self.assertIn('if saved_scanner_tf not in scanner_intervals:',setup)

    def test_initial_automatic_scan_respects_closed_exchange_window(self):
        scanner=function_source("auto_scan_loop")
        self.assertIn('if not refresh_hours():',scanner)
        self.assertNotIn('if not initial and not refresh_hours():',scanner)
        self.assertLess(scanner.index('if not refresh_hours():'),
                        scanner.index('try:await scan_market()'))
        self.assertIn('scan_next_refresh[0]=None',scanner)

    def test_partial_scanner_candles_are_retained_before_chart_publish(self):
        code=function_source("scan_market")
        self.assertIn('if prior.get("_scanner_timeframe")!=interval:',code)
        self.assertIn('hist=retain_candle_history(hist,prior,provider="Dhan")',code)
        self.assertLess(code.index('hist=retain_candle_history(hist,prior,provider="Dhan")'),
                        code.index('candles["scanner_chart_"+sym]=dict(hist'))
        old=[[10000+i*60,100,102,99,101,200] for i in range(35)]
        previous={"source":"Dhan","bars":old,"_scanner_timeframe":"1m"}
        new={"source":"Dhan","bars":old[-3:],"live_verified":False}
        shown=retain_candle_history(new,previous,provider="Dhan")
        self.assertEqual(shown["bars"],old)
        self.assertTrue(shown["historical"])
        self.assertFalse(shown["live_verified"])
        self.assertEqual(shown["freshness"],"historical_unverified")


if __name__=="__main__":
    unittest.main()
