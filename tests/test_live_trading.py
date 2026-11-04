"""No real broker requests: validate the real-order boundary with a fake broker."""
import asyncio
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from test_audit import start
from backend.live_trading import AngelTradingFeed, BrokerRejected, IST, LiveTrading, OrderJournal, TradingError
from backend.server import create_app
from fastapi.testclient import TestClient


class Broker(AngelTradingFeed):
    def __init__(self, now):
        super().__init__()
        self.now = now
        self.connect('key', 'ACCOUNT1234', 'pin', '123456')
        self.book = []
        self.position_rows = []
        self.placed = []
        self.cancelled = []
        self.failure = None
        self.cash = '100000'
        self.quote_age = 0
    def connect(self, key, client, pin, totp):
        self.key, self.client, self.token = key, client, 'BROKER_JWT_PRIVATE'
    def master(self):
        return [dict(name='NIFTY',symbol='NIFTY24NOV24000CE',exch_seg='NFO',instrumenttype='OPTIDX',expiry='24NOV2026',strike='2400000',token='999',lotsize='65',tick_size='5'),
                dict(name='SBIN',symbol='SBIN-EQ',exch_seg='NSE',instrumenttype='',expiry='',strike='0',token='3045',lotsize='1',tick_size='5')]
    def quotes(self, exchange, tokens):
        return [{'ltp':80 if tokens==['999'] else 800,'exchFeedTime':datetime.fromtimestamp(self.now[0]-self.quote_age,IST).strftime('%d-%b-%Y %H:%M:%S')}]
    def funds(self):return {'availablecash': self.cash}
    def positions(self):return self.position_rows
    def order_book(self):return self.book
    def place_limit(self, payload):
        self.placed.append(dict(payload))
        if self.failure:raise self.failure
        oid=str(100+len(self.placed))
        self.book.append(dict(payload,orderid=oid,status='open',filledshares='0',averageprice='0'))
        return {'orderid':oid}
    def cancel_order(self, order_id):self.cancelled.append(order_id);return {'orderid':order_id}


class LiveTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.now=[datetime(2026,11,5,10,tzinfo=IST).timestamp()]
        self.feed=Broker(self.now)
        self.journal=OrderJournal(Path(self.temp.name)/'orders.sqlite3')
        self.live=LiveTrading(self.feed,self.journal,enabled=True,clock=lambda:self.now[0])
        self.live.bind_account(self.feed.client)
        self.intent=dict(segment='Options',symbol='NIFTY',expiry='2026-11-24',strike=24000,option_type='CE',side='BUY',units=1,limit_price=80)
        self.live.arm('ENABLE LIVE TRADING')
    def submit(self, identity='a'*32):
        review=self.live.preview(self.intent)
        return self.live.submit(review['ticket'],identity,'PLACE REAL ORDER')

    def test_no_order_without_explicit_arm_review_and_confirmation(self):
        self.live.disarm()
        with self.assertRaises(TradingError):self.live.preview(self.intent)
        with self.assertRaises(TradingError):self.live.arm('yes')
        self.live.arm('ENABLE LIVE TRADING')
        review=self.live.preview(self.intent)
        with self.assertRaises(TradingError):self.live.submit(review['ticket'],'a'*32,'yes')
        self.assertFalse(self.feed.placed)

    def test_quantity_is_listed_lots_and_ack_is_not_a_fill(self):
        result=self.submit()
        self.assertEqual(self.feed.placed[0]['quantity'],'65')
        self.assertEqual(self.feed.placed[0]['ordertype'],'LIMIT')
        self.assertEqual(self.feed.placed[0]['producttype'],'INTRADAY')
        self.assertLess(len(self.feed.placed[0]['ordertag']),20)
        self.assertEqual(result['state'],'ACKNOWLEDGED');self.assertEqual(result['filled'],0)
        self.assertNotIn('BROKER_JWT_PRIVATE',str(result))

    def test_cash_quantity_and_invalid_contract(self):
        self.intent.update(segment='Cash',symbol='SBIN',limit_price=800,units=3)
        self.assertEqual(self.live.preview(self.intent)['quantity'],3)
        self.intent['symbol']='WRONG'
        with self.assertRaises(TradingError):self.live.preview(self.intent)

    def test_price_cash_tick_quantity_and_notional_guards(self):
        for changes in ({'limit_price':80.01},{'limit_price':200},{'limit_price':float('nan')},{'units':6},{'units':0},{'units':5}):
            with self.subTest(changes=changes),self.assertRaises(TradingError):self.live.preview(dict(self.intent,**changes))
        self.feed.cash='100'
        with self.assertRaises(TradingError):self.live.preview(self.intent)
        self.assertFalse(self.feed.placed)

    def test_stale_quote_after_hours_and_expired_preview(self):
        self.feed.quote_age=91
        with self.assertRaises(TradingError):self.live.preview(self.intent)
        self.feed.quote_age=0
        review=self.live.preview(self.intent)
        self.now[0]+=61
        with self.assertRaises(TradingError):self.live.submit(review['ticket'],'a'*32,'PLACE REAL ORDER')
        self.now[0]=datetime(2026,11,5,20,tzinfo=IST).timestamp()
        with self.assertRaises(TradingError):self.live.preview(self.intent)
        self.assertFalse(self.feed.placed)

    def test_revalidate_quote_and_position_before_submit(self):
        review=self.live.preview(self.intent)
        self.feed.quote_age=100
        with self.assertRaises(TradingError):self.live.submit(review['ticket'],'a'*32,'PLACE REAL ORDER')
        self.assertFalse(self.feed.placed)

    def test_duplicate_submit_and_consumed_ticket_do_not_send_again(self):
        review=self.live.preview(self.intent)
        first=self.live.submit(review['ticket'],'a'*32,'PLACE REAL ORDER')
        self.live.disarm()
        second=self.live.submit(review['ticket'],'a'*32,'PLACE REAL ORDER')
        self.assertEqual(first,second);self.assertEqual(len(self.feed.placed),1)
        self.live.arm('ENABLE LIVE TRADING')
        with self.assertRaises(TradingError):self.live.submit(review['ticket'],'b'*32,'PLACE REAL ORDER')

    def test_unknown_submit_survives_restart_and_blocks_resend(self):
        self.feed.failure=TimeoutError('PRIVATE')
        result=self.submit()
        self.assertEqual(result['state'],'UNKNOWN')
        restarted=LiveTrading(self.feed,OrderJournal(self.journal.path),enabled=True,clock=lambda:self.now[0])
        restarted.bind_account(self.feed.client);restarted.arm('ENABLE LIVE TRADING')
        with self.assertRaises(TradingError):restarted.preview(self.intent)
        self.assertEqual(restarted.submit('unused','a'*32,'PLACE REAL ORDER')['state'],'UNKNOWN')
        self.assertEqual(len(self.feed.placed),1)

    def test_timeout_reconciles_by_order_tag_without_resubmitting(self):
        self.feed.failure=TimeoutError()
        self.submit()
        self.feed.book=[dict(self.feed.placed[0],orderid='101',status='complete',filledshares='65',averageprice='80')]
        rows=self.live.reconcile()
        self.assertEqual(rows[0]['state'],'COMPLETE');self.assertEqual(rows[0]['filled'],65)
        self.assertEqual(len(self.feed.placed),1)

    def test_daily_entry_limit_is_durable(self):
        self.submit('a'*32);self.submit('b'*32)
        with self.assertRaises(TradingError):self.live.preview(self.intent)
        self.assertEqual(len(self.feed.placed),2)

    def test_sell_requires_filled_long_position_and_reserves_pending_exits(self):
        self.intent['side']='SELL'
        with self.assertRaises(TradingError):self.live.preview(self.intent)
        self.feed.position_rows=[dict(symboltoken='999',exchange='NFO',producttype='INTRADAY',netqty='65')]
        self.submit()
        with self.assertRaises(TradingError):self.live.preview(self.intent)
        self.assertEqual(len(self.feed.placed),1)

    def test_cancellation_does_not_claim_cancelled_or_close_a_position(self):
        self.submit()
        result=self.live.cancel('a'*32,'CANCEL REAL ORDER')
        self.assertEqual(result['state'],'CANCEL_REQUESTED')
        self.assertEqual(self.feed.cancelled,['101'])
        self.feed.book[0]['status']='cancelled'
        self.assertEqual(self.live.reconcile()[0]['state'],'CANCELLED')

    def test_rejected_submit_is_not_reported_as_filled(self):
        self.feed.failure=BrokerRejected('PRIVATE')
        result=self.submit()
        self.assertEqual(result['state'],'REJECTED');self.assertEqual(result['filled'],0)

    def test_server_endpoints_require_session_and_account_arm(self):
        pair='x'*48
        app=create_app(pair,self.feed,trading=self.live)
        with TestClient(app) as client:
            self.assertEqual(client.post('/v1/live/preview',json=self.intent).status_code,401)
            login=client.post('/v1/login',headers={'X-BotKing-Key':pair},json=dict(api_key='key',client_code='ACCOUNT1234',pin='1234',totp='123456'))
            self.assertEqual(login.status_code,200,login.text)
            headers={'Authorization':'Bearer '+login.json()['session']}
            self.assertFalse(client.post('/v1/live/capabilities',headers=headers).json()['armed'])
            self.assertEqual(client.post('/v1/live/preview',headers=headers,json=self.intent).status_code,400)
            self.assertEqual(client.post('/v1/live/arm',headers=headers,json={'confirmation':'ENABLE LIVE TRADING'}).status_code,200)
            review=client.post('/v1/live/preview',headers=headers,json=self.intent)
            self.assertEqual(review.status_code,200,review.text)
            payload={'ticket':review.json()['ticket'],'request_id':'a'*32,'confirmation':'PLACE REAL ORDER'}
            self.assertEqual(client.post('/v1/live/submit',headers=headers,json=payload).status_code,200)
            client.post('/v1/logout',headers=headers)
            self.assertFalse(self.live.capabilities()['armed'])

    def test_ui_never_submits_without_review_and_arm_does_not_submit(self):
        _,v=start({'scanner_live':False})
        ui=v['live_controls']
        with patch.object(v['angel_feed'],'live') as call:
            asyncio.run(ui.submit());asyncio.run(ui.arm())
            call.assert_not_called()
        self.assertIsNone(ui.review)

    def test_ui_consumes_review_on_uncertain_result(self):
        _,v=start({'scanner_live':False});ui=v['live_controls']
        ui.review={'data':{'ticket':'ticket'},'request_id':'a'*32,'epoch':v['angel_feed'].epoch}
        with patch.object(v['angel_feed'],'live',side_effect=FeedError('PRIVATE')) as call:
            asyncio.run(ui.submit());asyncio.run(ui.submit())
        submits=[args for args in call.call_args_list if args.args[0]=='submit']
        self.assertEqual(len(submits),1);self.assertIsNone(ui.review)


from market_feed import FeedError
