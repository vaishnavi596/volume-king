"""Regression checks for the Options layout and missing feed state."""
import unittest
import flet as ft
from test_audit import start

class OptionsLayoutTests(unittest.TestCase):
    def test_options_have_no_expanded_controls_in_scroll_or_wrap(self):
        _,v=start({'scanner_live':False})
        for name in ('chain_symbol','option_add_symbol','option_expiry_choice','expiry'):
            self.assertFalse(getattr(v[name],'expand',None),name)
        def walk(c):
            if isinstance(c,ft.Row) and c.wrap:
                for child in c.controls:
                    self.assertFalse(getattr(child,'expand',None))
            for child in c._get_children():walk(child)
        for control in v['options']():walk(control)

    def test_missing_option_feed_keeps_table_without_fabricated_prices(self):
        _,v=start({'scanner_live':False,'option_strike':'24000'})
        preview=v['option_chain_preview']()
        table=preview.controls[2].controls[0]
        self.assertEqual([cell.content.value for cell in table.rows[0].cells],
                         ['—','—','24000 (manual)','—','—'])
        self.assertEqual(len(table.columns),5)
        self.assertIn('not connected',preview.controls[3].value)
        v['quotes']['NIFTY']={'price':24123.45}
        self.assertIn('24,123.45',v['option_chain_preview']().controls[0].value)
