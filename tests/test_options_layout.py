"""Dhan-only Options UI regression tests; no Angel One or simulated premiums."""
import unittest
import flet as ft
from test_audit import start


def rendered_text(control):
    values = []
    def walk(item):
        if isinstance(item, ft.Text):
            values.append(str(item.value))
        for child in item._get_children():
            walk(child)
    walk(control)
    return " ".join(values)


class OptionsLayoutTests(unittest.TestCase):
    def test_option_chart_does_not_request_legacy_broker(self):
        _, v = start({"source": "Dhan", "scanner_live": False})
        shown = rendered_text(v["option_chart_panel"]())
        self.assertIn("Dhan CE/PE premium history", shown)
        self.assertIn("not available", shown)
        self.assertIn("Dhan data only", shown)
        self.assertNotIn("Connect Angel One in Settings", shown)
        self.assertEqual(v["option_chart_cache"], {})

    def test_option_chain_missing_data_is_not_fabricated(self):
        _, v = start({"source": "Dhan", "scanner_live": False})
        shown = rendered_text(v["option_chain_preview"]())
        self.assertIn("Dhan", shown)
        self.assertIn("Option-chain data not loaded", shown)
        self.assertIn("Missing strikes are not zero", shown)
        self.assertFalse(v["selected_option_rows"]())

    def test_options_have_visible_dhan_refresh(self):
        _, v = start({"source": "Dhan", "scanner_live": False})
        controls = v["options"]()
        labels = []
        def walk(c):
            if isinstance(c, ft.ElevatedButton):
                labels.append(str(c.text))
            for child in c._get_children():
                walk(child)
        for control in controls:
            walk(control)
        self.assertIn("Refresh Dhan Option Chain", labels)
        self.assertFalse(any("Connect Angel One in Settings" in rendered_text(control) for control in controls))

    def test_options_have_no_expanded_controls_in_scroll_or_wrap(self):
        _, v = start({"scanner_live": False})
        for name in ("chain_symbol", "option_add_symbol", "option_expiry_choice", "expiry"):
            self.assertFalse(getattr(v[name], "expand", None), name)
        def walk(c):
            if isinstance(c, ft.Row) and c.wrap:
                for child in c.controls:
                    self.assertFalse(getattr(child, "expand", None))
            for child in c._get_children():
                walk(child)
        for control in v["options"]():
            walk(control)

    def test_option_paper_action_remains_disabled_without_verified_contract(self):
        _, v = start({"source": "Dhan", "scanner_live": False})
        v["option_paper_action"]("BUY")
        self.assertIn("No order placed", v["option_paper_note"].value)
