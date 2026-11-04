"""Paper isolation, one-page live selection, and broker-only data routing."""
import asyncio
import time
import unittest
from unittest.mock import patch

from test_audit import start,event
from market_feed import FeedError

def controls(root):
    yield root
    for child in root._get_children():yield from controls(child)

class FivePageLiveTests(unittest.TestCase):
    def prepare_quote(self,v,age=0):
        v['expiry'].value='2026-12-01';v['option_expiry_choice'].value='Manual'
        v['sync_selected_live_context']()
        v['option_feed'].update(symbol=v['chain_symbol'].value,expiry=v['expiry'].value,
            rows=[dict(side='CE',strike=24000,premium=80,oi=100,volume=100,lot_size=65,timestamp=time.time()-age)])
        v['option_chain_preview']().controls[2].controls[0].rows[0].cells[0].on_tap(None)

    def test_five_pages_keep_paper_and_live_controls_separate(self):
        _,v=start({'scanner_live':False})
        self.assertEqual(v['names'],['Home','Live','Settings','Scanner','Paper'])
        self.assertEqual(len(v['navbar'].controls),5)
        for i in range(5):
            v['select'](i)
            items=[c for root in v['body'].controls for c in controls(root)]
            for name in ('sl','bot_premium','auto_entry','buy_dip','protection_enabled','option_qty'):
                self.assertEqual(v[name] in items,i==4,(i,name))
            self.assertEqual(v['live_controls'].phrase in items,i==1)
            self.assertEqual(v['source'] in items,i==2)
            self.assertEqual(len(items),len(set(map(id,items))))

    def test_fifth_page_and_paper_state_survive_restart(self):
        page,v=start({'scanner_live':False,'bot_lot_size':65})
        v['select'](4)
        _,restored=start(page.client_storage.get('bot_king_preferences'))
        self.assertEqual(restored['current'][0],4)
        self.assertEqual(restored['bot_lot_size'].value,'65')
        self.assertFalse(restored['live_controls'].ack.value)

    def test_chain_tap_populates_live_form_without_sending_an_order(self):
        _,v=start({'scanner_live':False})
        with patch.object(v['angel_feed'],'live') as call:
            self.prepare_quote(v);call.assert_not_called()
        ui=v['live_controls']
        self.assertEqual((ui.symbol.value,ui.expiry.value,ui.strike.value,ui.option_type.value,ui.price.value),('NIFTY','2026-12-01','24000','CE','80'))
        self.assertIsNone(ui.review)
        self.assertFalse(v['bot_position']['side'])

    def test_old_quote_does_not_become_live_limit_price(self):
        _,v=start({'scanner_live':False});self.prepare_quote(v,age=100)
        self.assertEqual(v['live_controls'].price.value,'')

    def test_symbol_change_clears_old_strike_price_and_confirmation(self):
        _,v=start({'scanner_live':False});self.prepare_quote(v)
        ui=v['live_controls'];ui.review={'old':True}
        v['chain_symbol'].value='TCS';v['chain_symbol'].on_change(event(v['chain_symbol']))
        self.assertEqual(ui.symbol.value,'TCS')
        self.assertEqual(ui.strike.value,'');self.assertEqual(ui.price.value,'')
        self.assertIsNone(ui.review)

    def test_manual_expiry_change_invalidates_live_review(self):
        _,v=start({'scanner_live':False});self.prepare_quote(v)
        ui=v['live_controls'];ui.review={'old':True}
        v['expiry'].value='2026-12-08';v['expiry'].on_change(event(v['expiry']))
        self.assertEqual(ui.expiry.value,'2026-12-08')
        self.assertEqual(ui.price.value,'');self.assertIsNone(ui.review)

    def test_live_strike_drives_chart_context_and_selection_persists(self):
        page,v=start({'scanner_live':False})
        ui=v['live_controls'];ui.strike.value='24100';ui.option_type.value='PE';ui.edited()
        self.assertEqual(v['option_chart_context']()[2:],('24100','PE'))
        _,restored=start(page.client_storage.get('bot_king_preferences'))
        self.assertEqual(restored['live_controls'].strike.value,'24100')
        self.assertEqual(restored['live_controls'].option_type.value,'PE')

    def test_broker_only_mode_does_not_silently_request_yahoo(self):
        _,v=start({'scanner_live':False,'source':'Broker API'})
        with patch.dict(v['get_yahoo'].__globals__,{'unexpected':None}):
            with patch.object(v['get_yahoo'].__globals__['urllib'].request,'urlopen') as network:
                with self.assertRaises(FeedError):v['get_market_data']('TCS','5m','7d')
                network.assert_not_called()

    def test_successful_api_login_selects_broker_data_and_does_not_arm_trading(self):
        _,v=start({'scanner_live':False,'source':'Auto'})
        def connect(*args):v['angel_feed'].key='test';v['angel_feed'].token='test'
        with patch.object(v['angel_feed'],'connect',side_effect=connect):asyncio.run(v['connect_angel']())
        self.assertEqual(v['source'].value,'Broker API')
        self.assertEqual(v['prefs']['source'],'Broker API')
        self.assertFalse(v['live_controls'].capabilities.get('armed'))
