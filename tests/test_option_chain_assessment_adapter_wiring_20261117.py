"""Offline source contract: Dhan chain exposes informational assessment rows."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OptionChainWiringTests(unittest.TestCase):
    def test_option_chain_uses_shared_adapter_without_extra_provider_call(self):
        module = ast.parse((ROOT / "backend" / "server.py").read_text(encoding="utf-8"))
        routes = [n for n in ast.walk(module) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                  and n.name == "dhan_option_chain"]
        self.assertEqual(len(routes), 1)
        route = routes[0]
        calls = [n for n in ast.walk(route) if isinstance(n, ast.Call)]
        names = [n.func.id for n in calls if isinstance(n.func, ast.Name)]
        self.assertIn("option_filter_rows", names)
        self.assertEqual(names.count("option_filter_rows"), 1)
        self.assertEqual(names.count("calculate_option_metrics"), 1)
        provider_calls = [n for n in calls if isinstance(n.func, ast.Attribute)
                          and n.func.attr == "option_chain"]
        self.assertEqual(len(provider_calls), 1)

    def test_no_trade_signal_or_score_in_adapter(self):
        source = (ROOT / "backend" / "assessment_filter_adapter.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        self.assertFalse(any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                             and n.func.attr in ("post", "order", "place_order")
                             for n in ast.walk(tree)))


if __name__ == "__main__":
    unittest.main()
