"""V3 Android boot wiring static regression: guards known phone failure triggers."""
import ast
from pathlib import Path
import unittest

SRC=Path(__file__).resolve().parents[1]/"src"/"main.py"

class TestPhoneStartup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text=SRC.read_text(encoding="utf-8")
        cls.tree=ast.parse(cls.text)
        cls.functions={}
        for fn in ast.walk(cls.tree):
            if isinstance(fn,(ast.FunctionDef,ast.AsyncFunctionDef)):
                cls.functions[fn.name]=ast.get_source_segment(cls.text,fn) or ""

    def test_scanner_cache_only_uses_shared_timeframe(self):
        body=self.functions["scan_market"]
        self.assertIn("shared_history(sym,interval)",body)
        self.assertIn('if not allow_network and prefs.get("source")=="Dhan"',body)
        self.assertIn("valid_candle_history(shared.get",body)
        self.assertIn("market_store.get(",body) # guarded fallback after same-timeframe shared history

    def test_default_options_refresh_after_successful_ssk_login(self):
        body=self.functions["check_clone_v2_connection"]
        self.assertIn('building_doctor.milestone("gateway_authorized")',body)
        self.assertIn('building_doctor.milestone("quotes_response_received")',body)
        self.assertIn("building_doctor.login_source_coverage",body)
        self.assertIn("page.run_task(refresh_selected_options)",body)
        self.assertIn("dhan_feed.activate_with_quote(proof)",body)
        self.assertLess(body.index("dhan_feed.activate_with_quote(proof)"),
                        body.index("page.run_task(refresh_selected_options)"))

    def test_option_provider_rate_limit_still_enforced(self):
        body=self.functions["refresh_selected_options"]
        self.assertIn('dhan_feed.cooldown_remaining("/dhan/option-expiries")',body)
        self.assertIn('dhan_feed.cooldown_remaining("/dhan/option-chain")',body)
        self.assertIn("await asyncio.sleep(3.25)",body)

    def test_no_automatic_network_from_capacity_buttons(self):
        body=self.functions["v3_live_building_panel"]
        self.assertIn("benchmark_cached_capacity",body)
        self.assertIn("asyncio.to_thread(benchmark_cached_capacity",body)
        self.assertNotIn("dhan_feed.intraday(",body)
        self.assertNotIn("clone_v2_gateway.market_quotes(",body)

if __name__=="__main__":
    unittest.main()
