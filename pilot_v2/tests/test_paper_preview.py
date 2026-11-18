"""V2-only non-executing paper risk calculator and Flet source gates."""
import ast
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(ROOT))
from paper_preview import preview_manual_paper_risk


class PaperPreviewTests(unittest.TestCase):
    def test_buy_and_sell_risk_with_pure_v1_engine(self):
        buy = preview_manual_paper_risk(
            "BUY", 100, 2, 2, 4, 10000, 1000, 5)
        self.assertEqual(buy["stop"], 98)
        self.assertEqual(buy["target"], 104)
        self.assertEqual(buy["planned_risk"], 4)
        self.assertFalse(buy["orders_enabled"])
        self.assertFalse(buy["live_verified"])
        sell = preview_manual_paper_risk(
            "SELL", 100, 2, 2, 4, 10000, 1000, 5)
        self.assertEqual(sell["stop"], 102)
        self.assertEqual(sell["target"], 96)

    def test_risk_excess_and_invalid_inputs_fail_closed(self):
        for value in ("nan", "inf", "-10", "", None):
            with self.subTest(value=value), self.assertRaises((ValueError, TypeError)):
                preview_manual_paper_risk("BUY", value, 2, 2, 4, 10000, 1000, 5)
        with self.assertRaises(ValueError):
            preview_manual_paper_risk("BUY", 100, 100, 3, 4, 100, 1, 1)
        with self.assertRaises(ValueError):
            preview_manual_paper_risk("BUY", 100, True, 2, 4, 10000, 1000, 5)
        with self.assertRaises(ValueError):
            preview_manual_paper_risk("HOLD", 100, 2, 2, 4, 10000, 1000, 5)

    def test_copied_engine_has_no_broker_network_or_order_calls(self):
        raw = (ROOT / "paper_engine.py").read_text()
        tree = ast.parse(raw)
        modules = [n.module for n in ast.walk(tree)
                   if isinstance(n, ast.ImportFrom)]
        modules += [a.name for n in ast.walk(tree)
                    if isinstance(n, ast.Import) for a in n.names]
        for name in ("requests", "httpx", "socket", "server_feed", "market_feed"):
            self.assertNotIn(name, modules)
        self.assertNotIn("place_order(", raw)
        self.assertNotIn("submit_order(", raw)

    def test_actual_settings_preview_wiring_and_no_execution(self):
        src = (ROOT / "main.py").read_text()
        ast.parse(src)
        for marker in ("from paper_preview import preview_manual_paper_risk",
                       "def calculate_paper_preview(e):",
                       "preview_manual_paper_risk(", 'label="Paper side"',
                       '"Calculate paper risk (no orders)"',
                       'paper_result[0]'):
            self.assertIn(marker, src)
        self.assertNotIn("place_order(", src)
        self.assertNotIn("submit_order(", src)
        self.assertEqual(src.count("ft.NavigationDestination("), 3)

if __name__ == "__main__":
    unittest.main()
