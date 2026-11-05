"""Offline regressions for the phone-reported connected-without-data failure."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import unittest
from unittest.mock import patch
import flet as ft
from test_audit import start
from market_feed import FeedError
from server_feed import ServerAngelFeed, ServerBusy
from option_activity import changes

def walk(c):
    yield c
    for child in c._get_children():yield from walk(child)

class ConnectionReleaseTests(unittest.TestCase):
    def connected(self,v):
        v['angel_feed'].server='https://owner.example';v['angel_feed'].token='private-test-session'

    def test_nav_reorder_preserves_internal_saved_page_identity(self):
        _,v=start({'last_page':2,'scanner_live':False})
        self.assertEqual(v['current'][0],2)
        self.assertEqual(v['nav_order'],[0,1,3,4,2])
        v['navbar'].controls[-1].content.on_click(None)
        self.assertEqual(v['current'][0],2)

    def test_connected_credentials_hidden_and_restore_on_disconnect(self):
        _,v=start({'scanner_live':False});self.connected(v)
        v['select'](2)
        items=[c for root in v['body'].controls for c in walk(root)]
        self.assertNotIn(v['api_url'],items)
        for field in v['credential_inputs'].values():self.assertNotIn(field,items)
        labels=[c.value for c in items if isinstance(c,ft.Text)]
        self.assertIn('Angel One API — Connected',labels)
        self.assertTrue(any('quote time unavailable' in x for x in labels))
        v['angel_feed'].disconnect();v['select'](2)
        items=[c for root in v['body'].controls for c in walk(root)]
        self.assertIn(v['api_url'],items)

    def test_underlying_survives_expiry_error_before_market_open(self):
        _,v=start({'scanner_live':False});self.connected(v)
        hist=dict(price=123,source='Angel One',quote_timestamp=time.time(),bars=[[1,1,2,1,1,1]])
        with patch.object(v['angel_feed'],'history',return_value=hist),patch.object(v['angel_feed'],'expiries',side_effect=FeedError('Listed expiry unavailable')):
            asyncio.run(v['refresh_selected_options']())
        self.assertEqual(v['quotes'][v['chain_symbol'].value]['price'],123)
        self.assertFalse(v['option_feed_busy'][0])
        self.assertIn('No listed expiry',v['option_feed_status'][0])

    def test_no_unwired_filter_broker_or_practice_mode_choices(self):
        _,v=start({'scanner_live':False,'mode':'Auto','broker':'Dhan'})
        self.assertEqual(v['mode'].value,'Paper')
        self.assertEqual([o.key for o in v['mode'].options],['Paper'])
        self.assertEqual([o.key for o in v['broker'].options],['Angel One'])
        self.assertNotIn('Max Pain',[o.key for o in v['filter_choice'].options])
        items=[c for root in v['paper_page']() for c in walk(root)]
        self.assertNotIn(v['squareoff'],items)

    def test_unknown_lifecycle_event_does_not_pause_open_app(self):
        page,v=start({'scanner_live':False})
        page.on_app_lifecycle_state_change(type('E',(),{'data':'unknown'})())
        self.assertTrue(v['app_active'][0])
        with patch.object(v['live_controls'],'pause'):
            page.on_app_lifecycle_state_change(type('E',(),{'data':'paused'})())
        self.assertFalse(v['app_active'][0])
        page.on_app_lifecycle_state_change(type('E',(),{'data':'resumed'})())
        self.assertTrue(v['app_active'][0])

    def test_paper_broker_price_never_sends_real_order_and_rejects_stale(self):
        _,v=start({'scanner_live':False,'bot_segment':'Cash','bot_symbol':'TCS'})
        self.connected(v)
        contract=v['bot_values']()[4]
        v['bot_position'].update(side='BUY',contract=contract,position_id='practice',entry=80,quantity=1)
        with patch.object(v['angel_feed'],'history',return_value=dict(price=81,quote_timestamp=time.time(),source='Angel One')),patch.object(v['angel_feed'],'live') as live:
            asyncio.run(v['paper_api_tick']())
            self.assertEqual(v['paper_mark'].value,'81.0');live.assert_not_called()
        # A different key avoids the short history request cache.
        v['provider_generation'][0]+=1
        with patch.object(v['angel_feed'],'history',return_value=dict(price=99,quote_timestamp=time.time()-100,source='Angel One')):
            asyncio.run(v['paper_api_tick']())
        self.assertEqual(v['paper_mark'].value,'81.0')
        self.assertIn('old',v['paper_api_status'].value)

    def test_snapshot_delta_needs_same_contract_session_and_newer_timestamp(self):
        row=dict(strike=100,side='CE',oi=10,premium=5,timestamp=100)
        old=dict(symbol='TCS',expiry='2026-11-24',source='Angel One',rows=[row])
        new=dict(old,rows=[dict(row,oi=13,premium=6,timestamp=110)])
        self.assertEqual(changes(new,old)[0]['oi_change'],3)
        self.assertNotIn('oi_change',changes(new,old,False)[0])
        self.assertNotIn('oi_change',changes(dict(new,expiry='other'),old)[0])
        self.assertNotIn('oi_change',changes(old,old)[0])

class TransportQueueTests(unittest.TestCase):
    def test_parallel_reads_queue_instead_of_colliding_on_gateway(self):
        feed=ServerAngelFeed();active=0;peak=0;mutex=threading.Lock()
        def call(*args):
            nonlocal active,peak
            with mutex:active+=1;peak=max(peak,active)
            time.sleep(.02)
            with mutex:active-=1
            return {'ok':True}
        with patch.object(feed,'_call_once',side_effect=call):
            with ThreadPoolExecutor(4) as pool:
                results=list(pool.map(lambda _:feed._call('/v1/history',{}),range(4)))
        self.assertEqual(peak,1);self.assertEqual(len(results),4)

    def test_retry_only_readonly_busy_response_never_submit(self):
        feed=ServerAngelFeed()
        with patch.object(feed,'_call_once',side_effect=[ServerBusy(),{'ok':True}]) as call,patch('server_feed.time.sleep'):
            self.assertTrue(feed._call('/v1/history',{})['ok']);self.assertEqual(call.call_count,2)
        with patch.object(feed,'_call_once',side_effect=ServerBusy()) as call:
            with self.assertRaises(ServerBusy):feed._call('/v1/live/submit',{})
            self.assertEqual(call.call_count,1)
