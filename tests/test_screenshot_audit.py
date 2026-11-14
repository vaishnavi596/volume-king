"""Screenshot audit regression contracts for the compact dashboard and scanner."""
import unittest
import flet as ft
from test_audit import start
from test_mobile_regressions import walk


class ScreenshotAuditTests(unittest.TestCase):
    def test_settings_has_collapsible_diagnostics(self):
        _, state = start({"scanner_live": False})
        state["select"](2)
        tiles = [c for root in state["body"].controls for c in walk(root) if isinstance(c, ft.ExpansionTile)]
        self.assertTrue(tiles, "Diagnostics must be available in Settings only")

    def test_scanner_still_exposes_all_ten_filters(self):
        _, state = start({"scanner_live": False})
        state["select"](3)
        text = " ".join(str(getattr(c, "label", None) or getattr(c, "value", None) or "") for root in state["body"].controls for c in walk(root) if isinstance(c, (ft.Text, ft.Checkbox)))
        for name in ("Supertrend", "EMA 9/21", "RSI 14", "MACD", "VWAP",
                     "SMC Structure", "Order Block", "Pivot Points", "FVG", "Liquidity Sweep"):
            self.assertIn(name, text)

    def test_six_destinations_preserved(self):
        _, state = start({"scanner_live": False})
        for index in range(6):
            state["select"](index)
            self.assertEqual(state["current"][0], index)


if __name__ == "__main__":
    unittest.main()
