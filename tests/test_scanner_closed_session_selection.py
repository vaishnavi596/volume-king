"""After-hours Dhan Scanner selection must not create broker history requests."""
import ast
import pathlib
import unittest
import asyncio
import sys
from types import SimpleNamespace

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"src"))
from candle_retention import valid_candle_history

source=(pathlib.Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
tree=ast.parse(source)
functions={node.name:node for node in ast.walk(tree)
           if isinstance(node,ast.AsyncFunctionDef) or isinstance(node,ast.FunctionDef)}


class ScannerClosedSessionCacheOnlyTests(unittest.TestCase):
    def test_selected_symbol_uses_cache_only_after_close(self):
        cb=ast.get_source_segment(source,functions["trigger_scan"])
        self.assertIn('page.run_task(scan_market, not (prefs.get("source")=="Dhan" and not refresh_hours()))',cb)
        self.assertIn("scan_generation[0]+=1",cb)

    def test_scan_market_has_local_only_path_before_provider_fetch(self):
        scan=ast.get_source_segment(source,functions["scan_market"])
        self.assertIn("async def scan_market(allow_network=True)",scan)
        self.assertIn('if not allow_network and prefs.get("source")=="Dhan":',scan)
        self.assertIn('valid_candle_history(selected.get("bars"))',scan)
        self.assertIn('valid_candle_history(saved.get("bars"))',scan)
        self.assertIn('freshness="historical_unverified"',scan)
        # The only direct provider fetch belongs in the explicit network branch.
        matches=[n for n in ast.walk(functions["scan_market"]) if isinstance(n,ast.Call)
                 and isinstance(n.func,ast.Attribute) and n.func.attr=="to_thread"
                 and n.args and isinstance(n.args[0],ast.Name)
                 and n.args[0].id=="get_market_data"]
        self.assertEqual(len(matches),1)
        self.assertTrue(any(isinstance(n,ast.If) and
            any(m is matches[0] for m in ast.walk(n)) and
            "allow_network" in ast.unparse(n.test)
            for n in ast.walk(functions["scan_market"])))

    def test_auto_restart_remains_closed_session_cache_only(self):
        fn=ast.get_source_segment(source,functions["restart_latest_scan"])
        self.assertIn("await scan_market(allow_network and not",fn)
        self.assertIn('prefs.get("source")=="Dhan" and not refresh_hours()',fn)
        scan=ast.get_source_segment(source,functions["scan_market"])
        self.assertIn("page.run_task(restart_latest_scan,allow_network)",scan)

    def test_real_cache_only_branch_never_calls_provider(self):
        # Execute the actual source's isolated history-selection branch, not
        # merely its spelling. No UI runtime or broker credentials involved.
        scan=functions["scan_market"]
        guarded=next(n for n in ast.walk(scan) if isinstance(n,ast.If)
                     and ast.unparse(n.test)==
                     "not allow_network and prefs.get('source') == 'Dhan'")
        method=ast.AsyncFunctionDef(
            name="select_history",args=ast.arguments(posonlyargs=[],args=[
                ast.arg(arg="allow_network")],vararg=None,kwonlyargs=[],
                kw_defaults=[],kwarg=None,defaults=[]),
            body=[guarded,ast.Return(value=ast.Name(id="hist",ctx=ast.Load()))],
            decorator_list=[])
        module=ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[]))
        rows=[[1795000000+i*180,100+i,101+i,99+i,100+i,1200]
              for i in range(36)]
        selected={"source":"Dhan","bars":rows,"_scanner_timeframe":"3m"}
        calls=[]
        def deny_fetch(*args):
            calls.append(args)
            raise AssertionError("Unexpected provider fetch")
        env={"prefs":{"source":"Dhan"},"sym":"RELIANCE","interval":"3m",
             "period":"7d","candles":{"scanner_chart_RELIANCE":selected},
             "market_store":SimpleNamespace(get=lambda *args:{}),
             "valid_candle_history":valid_candle_history,
             "get_market_data":deny_fetch,"asyncio":asyncio,
             "shared_history":lambda sym,tf:{} }
        exec(compile(module,"<scanner-history-branch>","exec"),env)
        result=asyncio.run(env["select_history"](False))
        self.assertEqual(result["bars"],rows)
        self.assertTrue(result["cached"])
        self.assertFalse(result["live_verified"])
        self.assertEqual(result["freshness"],"historical_unverified")
        self.assertEqual(calls,[])
        env["candles"].clear()
        # App restart: the in-memory selected chart is gone, but the
        # persisted same-provider/symbol/interval candle history remains.
        saved=dict(selected)
        lookups=[]
        def read_saved(*args):
            lookups.append(args)
            return saved
        env["market_store"]=SimpleNamespace(get=read_saved)
        # Rebind the function's global so this is the real second fallback.
        result=asyncio.run(env["select_history"](False))
        self.assertEqual(result["bars"],rows)
        self.assertTrue(result["cached"])
        self.assertEqual(lookups,[("market","Dhan","RELIANCE","3m","7d")])
        self.assertEqual(calls,[])
        # A persisted history that is too short must fail closed as well.
        saved["bars"]=rows[:2]
        env["scan_status"]=SimpleNamespace(value="")
        env["scan_shared"]={}
        env["scan_result"]=SimpleNamespace(controls=[])
        env["section"]=lambda title, contents: (title, contents)
        env["ft"]=SimpleNamespace(Column=lambda children,spacing: children)
        env["unavailable"]=lambda text: text
        env["note"]=lambda text: text
        self.assertIsNone(asyncio.run(env["select_history"](False)))
        self.assertIn("auto scan WAIT",env["scan_status"].value)
        self.assertEqual(env["scan_shared"]["direction"],"WAIT")
        self.assertEqual(calls,[])

    def test_last_session_analysis_is_separate_from_live_wait(self):
        scan=ast.get_source_segment(source,functions["scan_market"])
        self.assertIn('market_store.put("analysis_last_good",("Dhan",sym,interval),historical)',scan)
        self.assertIn('market_store.get("analysis_last_good","Dhan",sym,interval)',scan)
        self.assertIn('historical_bars=historical_regular_session_bars(bars,interval)',scan)
        self.assertIn('historical=analyze(historical_bars,selected=active_analysis_filters(),timeframe=interval)',scan)
        self.assertIn('historical.get("count",0)>=30',scan)
        self.assertIn('now=historical_bars[-1][0]+timeframe_spec(interval)["seconds"]',scan)
        self.assertIn('historical.get("timestamp")==historical_bars[-1][0]',scan)
        self.assertIn('vote_display(signal_percentages(shown_analysis),False,interval)',scan)
        self.assertIn('shown_analysis=(historical if history_valid',scan)
        self.assertIn('LAST SESSION HIST',scan)
        self.assertIn('live_verified=False,freshness="historical_unverified"',scan)
        self.assertIn('display_mode=resolve_mode(',scan)
        self.assertIn('session_eligible=regular_hours()',scan)
        self.assertIn('live_verified=live_source_verified',scan)
        self.assertIn('if display_mode!="LIVE":',scan)
        self.assertIn('if history_valid and display_mode=="HIST":',scan)

    def test_plain_max_pain_is_not_an_independent_filter(self):
        from scanner_engine import ALL_FILTERS, OPTION_FILTERS
        self.assertIn("Dhan Max Pain",OPTION_FILTERS)
        self.assertEqual(ALL_FILTERS.count("Dhan Max Pain"),1)
        self.assertNotIn("Max Pain",ALL_FILTERS)
        body=ast.get_source_segment(source,functions["scan_market"])
        self.assertIn("enrich_context_filter_rows",body)
        self.assertIn('market_store.put("analysis_last_good"',body)

    def test_option_context_never_votes_without_verified_evidence(self):
        from scanner_engine import OPTION_FILTERS
        match=ast.get_source_segment(source,functions["matching_option_context_for_symbol"])
        enrich=ast.get_source_segment(source,functions["enrich_context_filter_rows"])
        self.assertIn('data.get("symbol")==sym',match)
        self.assertIn('data.get("expiry")==listed',match)
        self.assertIn('sym!=chain_symbol.value or listed==expiry.value',match)
        self.assertIn('data.get("source")=="dhan"',match)
        self.assertIn('data.get("signal_eligible") is False',match)
        self.assertIn('row["vote"]=None',enrich)
        for name in OPTION_FILTERS:
            self.assertIn(name,("OI Support","OI Resistance","OI Profile","Dhan Max Pain"))
        self.assertIn('No matching Dhan expiry snapshot',enrich)

    def test_dhan_option_history_persists_only_exact_expiry_context(self):
        refresh=ast.get_source_segment(source,functions["refresh_selected_options"])
        match=ast.get_source_segment(source,functions["matching_option_context_for_symbol"])
        worker='await asyncio.to_thread(market_store.put,"option_context_last_good",("Dhan",sym,chosen),dict(data))'
        self.assertIn(worker,refresh)
        before,after=refresh.split(worker,1)
        self.assertIn('data.get("source")=="dhan"',before)
        self.assertIn('data.get("symbol")==sym',before)
        self.assertIn('data.get("expiry")==chosen',before)
        self.assertIn('data.get("signal_eligible") is False',before)
        self.assertIn('if generation!=provider_generation[0] or sym!=chain_symbol.value or choice!=option_expiry_choice.value or expiry.value!=chosen:return',after)
        self.assertIn('data.get("signal_eligible") is False',refresh)
        self.assertIn('market_store.get("option_context_last_good","Dhan",sym,listed)',match)
        self.assertIn('saved.get("expiry")==listed',match)
        self.assertIn('saved.get("symbol")==sym',match)
        self.assertIn('saved.get("source")=="dhan"',match)
        self.assertIn('live_verified=False',match)

    def test_manual_run_scan_keeps_explicit_network_option(self):
        manual=ast.get_source_segment(source,functions["run_scan"])
        self.assertIn("page.run_task(scan_market)",manual)


if __name__=="__main__":
    unittest.main()
