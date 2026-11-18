"""After-hours Dhan Scanner selection must not create broker history requests."""
import ast
import pathlib
import unittest

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
                 and isinstance(n.func,ast.Name) and n.func.id=="get_market_data"]
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

    def test_manual_run_scan_keeps_explicit_network_option(self):
        manual=ast.get_source_segment(source,functions["run_scan"])
        self.assertIn("page.run_task(scan_market)",manual)


if __name__=="__main__":
    unittest.main()
