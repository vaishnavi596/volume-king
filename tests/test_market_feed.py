import asyncio
import time
import unittest
from unittest.mock import patch
from test_audit import start
from market_feed import AngelFeed,FeedError

class FeedTests(unittest.TestCase):
    def test_broker_failure_never_uses_other_provider(self):
        _,v=start({'source':'Broker API','scanner_live':False})
        feed=v['angel_feed'];feed.key='test';feed.token='test'
        with patch.object(feed,'history',side_effect=FeedError('offline')) as broker:
            with patch('urllib.request.urlopen',side_effect=AssertionError('No external provider allowed')):
                with self.assertRaises(FeedError):v['get_market_data']('NIFTY')
            self.assertEqual(broker.call_count,1)
        feed.disconnect()
        with self.assertRaises(FeedError):v['get_market_data']('NIFTY')

    def test_disconnected_feed_is_unavailable_not_fallback(self):
        _,v=start({'source':'Broker API','scanner_live':False})
        with patch('urllib.request.urlopen',side_effect=AssertionError('No external provider allowed')):
            with self.assertRaises(FeedError):v['get_market_data']('NIFTY')
        self.assertEqual(v['health'].get('market:Broker API:NIFTY:5m')['state'],'UNAVAILABLE')

    def test_broker_success_is_preferred_without_yahoo(self):
        _,v=start({'source':'Auto','scanner_live':False})
        feed=v['angel_feed'];feed.key='test';feed.token='test'
        with patch.object(feed,'history',return_value={'source':'Angel One','bars':[]}),patch('urllib.request.urlopen',side_effect=AssertionError('Yahoo must not run')):
            self.assertEqual(v['get_market_data']('NIFTY')['source'],'Angel One')

    def test_no_order_endpoints_and_disconnect_clears_session(self):
        feed=AngelFeed();feed.key='test';feed.token='test'
        with self.assertRaises(FeedError):feed.request('placeOrder',{})
        feed.disconnect();self.assertFalse(feed.connected)
        self.assertFalse(feed.key);self.assertFalse(feed.token)
        with self.assertRaises(FeedError):feed.connect('','','','')

    def test_partial_stale_and_selected_window_pcr(self):
        _,v=start({'scanner_live':False})
        rows=[{'strike':24000,'side':side,'premium':100,'oi':oi,'timestamp':time.time()} for side,oi in [('CE',100),('PE',200)]]
        v['option_feed'].update(symbol=v['chain_symbol'].value,expiry=v['expiry'].value,rows=rows,complete=True)
        self.assertIn('2.000',v['option_metrics']('PCR').value)
        self.assertIn('not full chain',v['option_metrics']('PCR').value)
        v['option_feed']['complete']=False
        self.assertIn('incomplete',v['option_metrics']('PCR').value)
        rows[0]['timestamp']=time.time()-1000
        self.assertIn('old',v['option_metrics']('PCR').value)
        v['option_feed']['symbol']='WRONG'
        self.assertFalse(v['selected_option_rows']())

    def test_option_fetch_does_not_publish_after_selection_change(self):
        _,v=start({'source':'Auto','scanner_live':False})
        async def delayed(*args):
            v['chain_symbol'].value='BANKNIFTY'
            return {'price':100,'bars':[]}
        with patch('asyncio.to_thread',side_effect=delayed):
            asyncio.run(v['refresh_selected_options']())
        self.assertNotIn('NIFTY',v['quotes'])
        self.assertFalse(v['option_feed_busy'][0])

    def test_broker_timestamp_requires_timezone_and_finite_quotes(self):
        feed=AngelFeed()
        self.assertIsNotNone(feed.timestamp('2026-11-04T09:15:00+05:30'))
        self.assertIsNone(feed.timestamp('bad'))
        with self.assertRaises(FeedError):feed.number('nan')
        with self.assertRaises(FeedError):feed.number('inf')
        with self.assertRaises(FeedError):feed.nonnegative(-1)

    def test_exact_broker_contract_mapping_and_partial_quote_coverage(self):
        feed=AngelFeed();feed.key='test';feed.token='test'
        feed.instruments=[{'name':'NIFTY','exch_seg':'NFO','instrumenttype':'OPTIDX',
                           'expiry':'01DEC2099','strike':'2400000','symbol':'NIFTY01DEC9924000'+side,
                           'token':str(i),'lotsize':'25'} for i,side in enumerate(('CE','PE'),1)]
        with patch.object(feed,'quotes',return_value=[{'symbolToken':'1','ltp':100,'opnInterest':123,'tradeVolume':10,'exchFeedTime':'04-Nov-2026 09:15:00'}]):
            result=feed.option_chain('NIFTY','2099-12-01',24000)
        self.assertFalse(result['complete']);self.assertEqual(result['rows'][0]['strike'],24000)
        self.assertEqual(result['rows'][0]['lot_size'],25)
        self.assertEqual(feed.expiries('NIFTY'),['2099-12-01'])
        with self.assertRaises(FeedError):feed.option_chain('NIFTY','2099-12-02',24000)

    def test_stale_broker_quote_cannot_be_claimed_as_live(self):
        feed=AngelFeed();feed.key='test';feed.token='test'
        with patch.object(feed,'resolve',return_value=('NSE','123')),patch.object(feed,'request',return_value=[['2026-11-04T09:15:00+05:30',100,101,99,100,10]]),patch.object(feed,'quotes',return_value=[{'ltp':100,'exchFeedTime':'01-Jan-2000 09:15:00'}]):
            result=feed.history('NIFTY','5m','7d')
            self.assertTrue(result['historical_only'])
            self.assertEqual(len(result['bars']),1)
            self.assertEqual(result['source'],'Angel One')
            self.assertFalse(result['quote_unavailable'])

    def test_quote_failure_keeps_verified_candles_without_live_claim(self):
        feed=AngelFeed();feed.key='test';feed.token='test'
        with patch.object(feed,'resolve',return_value=('NSE','123')),patch.object(feed,'request',return_value=[['2026-11-04T09:15:00+05:30',100,101,99,100,10]]),patch.object(feed,'quotes',side_effect=FeedError('quote endpoint unavailable')):
            result=feed.history('NIFTY','5m','7d')
            self.assertTrue(result['historical_only'])
            self.assertTrue(result['quote_unavailable'])
            self.assertEqual(result['price'],100)
            self.assertIsNone(result['quote_timestamp'])
            self.assertEqual(len(result['bars']),1)
