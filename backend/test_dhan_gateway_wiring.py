"""Offline structural regression gates for the Dhan consent-to-market-data path.

These tests inspect source only. They never import/start the gateway, read real
credentials, contact Dhan, modify Oracle or enable orders.
"""
import ast
from pathlib import Path
import unittest


SERVER = Path(__file__).with_name("server.py")


class DhanGatewayWiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = ast.parse(SERVER.read_text(encoding="utf-8"), filename=str(SERVER))
        cls.create_app = next(
            n for n in cls.tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "create_app"
        )
        cls.functions = {
            n.name: n for n in cls.create_app.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

    def calls(self, function_name, called_name):
        function = self.functions[function_name]
        return any(
            isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and n.func.id == called_name
            for n in ast.walk(function)
        )

    def test_all_market_data_routes_share_token_selector(self):
        for name in ("dhan_ltp", "dhan_ltp_batch", "dhan_intraday"):
            with self.subTest(route=name):
                self.assertTrue(self.calls(name, "dhan_market_token"))

    def test_callback_invokes_opt_in_persistence_bridge(self):
        self.assertTrue(self.calls("dhan_callback", "_persist_dhan_consent_if_enabled"))

    def test_file_fallback_uses_configurable_path_and_strict_switch(self):
        function = self.functions["dhan_market_token"]
        source = ast.get_source_segment(SERVER.read_text(encoding="utf-8"), function)
        self.assertIn("DHAN_TOKEN_FILE", source)
        self.assertIn("DHAN_REQUIRE_VERIFIED_FILE_TOKEN", source)
        self.assertIn("select_persisted_token", source)

    def test_market_data_routes_do_not_read_hardcoded_token_file(self):
        for name in ("dhan_ltp", "dhan_ltp_batch", "dhan_intraday"):
            source = ast.get_source_segment(
                SERVER.read_text(encoding="utf-8"), self.functions[name]
            )
            with self.subTest(route=name):
                self.assertNotIn("/etc/bot-king/dhan-token", source)
                self.assertNotIn("read_text(", source)


if __name__ == "__main__":
    unittest.main()
