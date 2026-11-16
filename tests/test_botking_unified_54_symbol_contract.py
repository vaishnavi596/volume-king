"""Guard the fixed BOT KING 54-symbol market-data coverage contract.

51 NSE cash equities + 3 indices. This is NOT a blanket F&O entitlement
claim: equity option expiry/chain/PCR still require per-underlying evidence.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
INDEX = {"NIFTY", "BANKNIFTY", "SENSEX"}


def list_literal_assignment(filename, var):
    tree = ast.parse((ROOT / filename).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == var for t in node.targets
        ) and isinstance(node.value, (ast.List, ast.Tuple)):
            return ast.literal_eval(node.value)
    raise AssertionError(f"Missing static {var} roster")


def feed_roster():
    tree = ast.parse((ROOT / "src/server_feed.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "DHAN_VERIFIED_SYMBOLS"
            for t in node.targets
        ):
            call = node.value
            if isinstance(call, ast.Call) and len(call.args) == 1:
                return set(ast.literal_eval(call.args[0]))
    raise AssertionError("Missing verified feed roster")


class Unified54CoverageTests(unittest.TestCase):
    def test_exact_51_equities_plus_three_indices(self):
        equities = list_literal_assignment("src/main.py", "watch_symbols")
        symbols = feed_roster()
        self.assertEqual(len(equities), 51)
        self.assertEqual(len(set(equities)), 51)
        self.assertFalse(INDEX.intersection(equities))
        self.assertEqual(len(symbols), 54)
        self.assertEqual(symbols, set(equities) | INDEX)

    def test_shared_assessment_contract_not_index_only(self):
        source = (ROOT / "src/server_feed.py").read_text(encoding="utf-8")
        ui = (ROOT / "src/shared_assessment_ui.py").read_text(encoding="utf-8")
        self.assertIn('def assessment(self, symbol):', source)
        self.assertIn('def assessment_lines(symbol, cached,', ui)
        self.assertNotIn('if symbol in ("NIFTY", "BANKNIFTY", "SENSEX"):', ui)

    def test_broker_option_eligibility_is_not_conflated_with_cash_mapping(self):
        source = (ROOT / "backend/option_underlying_status.py").read_text(encoding="utf-8")
        self.assertIn('"expiry_verified": False', source)
        self.assertIn('"chain_verified": False', source)
        self.assertIn('"pcr_verified": False', source)
        self.assertIn('"network_requests": 0', source)


if __name__ == "__main__":
    unittest.main()
