import asyncio
import unittest
from unittest.mock import patch

import flet as ft
from test_audit import start


class FullAuditFixes(unittest.TestCase):
    def test_negated_and_uncertain_headlines_cannot_vote(self):
        _,v=start({'scanner_live':False})
        data=v['headline_signal']([{'title':'Company denies fraud allegations'}, {'title':'Rumour: company may default on loans'}])
        self.assertEqual(data['bias'],'UNCLASSIFIED')
        self.assertEqual(data['negative'],0)

    def test_hidden_fields_have_hidden_help_wrappers(self):
        _,v=start({'scanner_live':False})
        v['select'](3)
        def contains(control,target):return control is target or any(contains(c,target) for c in control._get_children())
        def walk(control):
            if getattr(control,'data',None)=='help_wrapper':
                for name in ('scan_min','scan_max'):
                    if contains(control,v[name]):self.assertFalse(control.visible)
            for child in control._get_children():walk(child)
        for control in v['body'].controls:walk(control)

    def test_long_field_labels_wrap_above_field(self):
        _,v=start({'scanner_live':False})
        field=ft.TextField(label='Maximum planned risk per position in rupees')
        wrapper=v['decorate_help'](field)
        self.assertEqual(field.label,'')
        self.assertTrue(field._bk_external_label)
        self.assertEqual(field._bk_help_label.value,'Maximum planned risk per position in rupees')
        self.assertIsInstance(wrapper.controls[0],ft.Column)

    def test_invalid_server_address_is_not_saved_or_sent(self):
        _,v=start({'scanner_live':False})
        v['api_url'].value='NOT_AN_ADDRESS'
        self.assertFalse(v['save_control'](v['api_url'],'api_url'))
        self.assertNotEqual(v['prefs']['api_url'],'NOT_AN_ADDRESS')
        with patch.object(v['angel_feed'],'connect') as connect:
            asyncio.run(v['connect_angel']());connect.assert_not_called()
        self.assertIn('HTTPS',v['api_url'].error_text)

    def test_disconnected_status_and_preview_expiry_do_not_claim_missing_adapter_or_verified_date(self):
        _,v=start({'scanner_live':False})
        self.assertNotIn('adapter required',v['connection_status'].value)
        v['option_expiry_note'].value='Expiry selected from Angel One instrument master'
        v['refresh_option_expiry']()
        self.assertIn('preview',v['option_expiry_note'].value)
        self.assertNotIn('selected from Angel One',v['option_expiry_note'].value)

    def test_obsolete_option_failure_does_not_override_new_symbol(self):
        _,v=start({'scanner_live':False,'option_expiry_choice':'Manual','option_expiry':'2026-12-01'})
        v['angel_feed'].key='test';v['angel_feed'].token='test'
        async def fail(*args):
            v['chain_symbol'].value='BANKNIFTY'
            raise TimeoutError()
        with patch('asyncio.to_thread',side_effect=fail):asyncio.run(v['refresh_selected_options']())
        self.assertNotIn('Feed unavailable',v['option_feed_status'][0])

    def test_old_option_quotes_are_not_marked_available(self):
        _,v=start({'scanner_live':False,'option_expiry_choice':'Manual','option_expiry':'2026-12-01'})
        v['angel_feed'].key='test';v['angel_feed'].token='test'
        old={'symbol':v['chain_symbol'].value,'expiry':v['expiry'].value,'rows':[{'side':'CE','strike':24000,'premium':80,'oi':100,'volume':100,'timestamp':1,'lot_size':25}],'complete':True,'source':'Angel One'}
        async def fake(func,*args):
            return old if func==v['angel_feed'].option_chain else {'price':24000,'bars':[],'source':'Yahoo Finance'}
        with patch('asyncio.to_thread',side_effect=fake):asyncio.run(v['refresh_selected_options']())
        key='options:'+v['chain_symbol'].value+':'+v['expiry'].value
        self.assertEqual(v['health'].get(key)['state'],'STALE')
