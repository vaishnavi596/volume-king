"""Regression checks for the Options layout and missing feed state."""
import unittest
import asyncio
import time
from unittest.mock import patch
import flet as ft
from test_audit import start
from market_feed import FeedError

class OptionsLayoutTests(unittest.TestCase):
    def chart_text(self, v):
        values=[]
        def walk(control):
            if isinstance(control,ft.Text):values.append(control.value)
            for child in control._get_children():walk(child)
        walk(v['option_chart_panel']())
        return ' '.join(values)

    def connected(self, v):
        v['angel_feed'].key='TEST';v['angel_feed'].token='TEST'
        v['source'].value='Broker API'
        v['prefs']['source']='Broker API'
        v['expiry'].value='2026-12-01'

    def test_connected_chart_empty_state_does_not_blame_yahoo(self):
        _,v=start({'scanner_live':False})
        self.connected(v)
        self.assertIn('Enter a listed strike',self.chart_text(v))
        self.assertNotIn('Yahoo',self.chart_text(v))
        self.assertIsNone(v['option_qty'].width)
        self.assertIsNone(v['option_side'].width)

    def test_chart_validates_selection_before_network_request(self):
        _,v=start({'scanner_live':False,'option_strike':''})
        self.connected(v)
        with patch.object(v['angel_feed'],'option_history') as request:
            asyncio.run(v['load_option_history']())
            request.assert_not_called()
        self.assertIn('positive listed strike',self.chart_text(v))

    def test_chart_failure_is_truthful_and_does_not_leak_exception(self):
        _,v=start({'scanner_live':False,'option_strike':'56000'})
        self.connected(v)
        with patch.object(v['angel_feed'],'option_history',side_effect=FeedError('PRIVATE_TOKEN')):
            asyncio.run(v['load_option_history']())
        message=self.chart_text(v)
        self.assertIn('Angel One option history request failed',message)
        self.assertNotIn('Yahoo',message)
        self.assertNotIn('PRIVATE_TOKEN',message)
        self.assertFalse(v['option_chart_busy'][0])

    def test_chart_loading_and_success_and_changed_selection(self):
        _,v=start({'scanner_live':False,'option_strike':'56000'})
        self.connected(v)
        bars=[[time.time()-600,80,82,79,81,10],[time.time()-300,81,83,80,82,20]]
        def fetch(*args):
            self.assertTrue(v['option_chart_busy'][0])
            self.assertIn('Loading selected option history',self.chart_text(v))
            return bars
        with patch.object(v['angel_feed'],'option_history',side_effect=fetch):
            asyncio.run(v['load_option_history']())
        self.assertEqual(v['option_chart_cache']['bars'],bars)
        self.assertIn('history loaded from Angel One',self.chart_text(v))
        v['option_strike'].value='56100'
        self.assertNotIn('history loaded',self.chart_text(v))
        self.assertIn('Enter a listed strike',self.chart_text(v))

    def test_old_chart_response_cannot_publish_for_new_selection(self):
        _,v=start({'scanner_live':False,'option_strike':'56000'})
        self.connected(v)
        def fetch(*args):
            v['option_strike'].value='56100'
            return [[1,1,1,1,1,1],[2,2,2,2,2,2]]
        with patch.object(v['angel_feed'],'option_history',side_effect=fetch):
            asyncio.run(v['load_option_history']())
        self.assertFalse(v['option_chart_cache'])
        self.assertNotIn('history loaded',self.chart_text(v))

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
        _,v=start({'scanner_live':False,'source':'Yahoo Finance','option_strike':'24000'})
        preview=v['option_chain_preview']()
        table=preview.controls[2].controls[0]
        self.assertEqual([cell.content.value for cell in table.rows[0].cells],
                         ['—','—','24000 (manual)','—','—'])
        self.assertEqual(len(table.columns),5)
        self.assertIn('not connected',preview.controls[3].value)
        v['quotes']['NIFTY']={'price':24123.45,'source':'Yahoo Finance'}
        self.assertIn('24,123.45',v['option_chain_preview']().controls[0].value)
