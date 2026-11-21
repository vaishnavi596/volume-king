import asyncio
import time
import unittest
from unittest.mock import patch
from test_audit import start
from market_feed import AngelFeed,FeedError

class FeedTests(unittest.TestCase):
    def test_legacy_auto_selection_migrates_to_dhan(self):
        _,v=start({'source':'Auto','scanner_live':False})
        self.assertEqual(v['prefs']['source'],'Dhan')
        with self.assertRaises(FeedError):
            v['get_market_data']('NIFTY')

    def test_legacy_yahoo_preference_migrates_to_dhan_without_yahoo_request(self):
        _,v=start({'source':'Yahoo Finance','scanner_live':False})
        self.assertEqual(v['prefs']['source'],'Dhan')
        with patch.dict(v['get_market_data'].__globals__,{'get_yahoo':lambda *args:(_ for _ in ()).throw(AssertionError('Yahoo must not run'))}):
            with self.assertRaisesRegex(FeedError,'Dhan disconnected'):
                v['fetch_market_data_uncached']('NIFTY')

    def test_legacy_broker_preference_never_activates_angel_or_yahoo(self):
        _,v=start({'source':'Broker API','scanner_live':False})
        self.assertEqual(v['prefs']['source'],'Dhan')
        feed=v['angel_feed']
        with patch.object(feed,'history',side_effect=AssertionError('Angel must not run')) as broker, patch.dict(v['get_market_data'].__globals__,{'get_yahoo':lambda *args:(_ for _ in ()).throw(AssertionError('Yahoo must not run'))}):
            with self.assertRaisesRegex(FeedError,'Dhan disconnected'):
                v['get_market_data']('NIFTY')
        broker.assert_not_called()

    def test_no_order_endpoints_and_disconnect_clears_session(self):
        feed=AngelFeed();feed.key='test';feed.token='test'
        with self.assertRaises(FeedError):feed.request('placeOrder',{})
        feed.disconnect();self.assertFalse(feed.connected)
        self.assertFalse(feed.key);self.assertFalse(feed.token)
        with self.assertRaises(FeedError):feed.connect('','','','')

    def test_injected_legacy_provider_never_reaches_internet(self):
        # A legacy setting or an unexpected callback must not bypass the
        # V3 Dhan-only network boundary, even without UI normalization.
        for provider in ('Yahoo Finance','Broker API','Unknown'):
            with self.subTest(provider=provider):
                _,v=start({'scanner_live':False,'source':'Dhan'})
                v['prefs']['source']=provider
                with patch('urllib.request.urlopen',side_effect=AssertionError('Unexpected outbound HTTP')) as network, patch.dict(
                    v['fetch_market_data_uncached'].__globals__,
                    {'get_yahoo':lambda *args:(_ for _ in ()).throw(AssertionError('Yahoo transport invoked'))}
                ):
                    with self.assertRaisesRegex(FeedError,'Dhan-only provider required'):
                        v['fetch_market_data_uncached']('NIFTY','1m','7d')
                network.assert_not_called()

    def test_injected_angel_login_callback_is_disabled_without_network(self):
        _,v=start({'scanner_live':False,'source':'Dhan'})
        v['broker'].value='Angel One'  # Direct callback injection, not a UI option.
        with patch.object(v['angel_feed'],'connect',side_effect=AssertionError('Angel login attempted')) as login, \
             patch('urllib.request.urlopen',side_effect=AssertionError('Unexpected network')) as network:
            asyncio.run(v['connect_angel']())
        login.assert_not_called()
        network.assert_not_called()
        self.assertIn('Angel One login disabled',v['connection_status'].value)

    def test_dhan_option_metrics_never_reuse_legacy_angel_window(self):
        _,v=start({'source':'Dhan','scanner_live':False})
        rows=[{'strike':24000,'side':side,'premium':100,'oi':oi,'timestamp':time.time()}
              for side,oi in [('CE',100),('PE',200)]]
        v['option_feed'].update(symbol=v['chain_symbol'].value,
                                expiry=v['expiry'].value,rows=rows,complete=True)
        self.assertFalse(v['selected_option_rows']())
        self.assertIn('not ready',v['option_metrics']('PCR').value)
        v['dhan_option_metrics'].update(source='dhan',symbol=v['chain_symbol'].value,
            expiry=v['expiry'].value,pcr=0.83049,max_pain=25100.0,
            freshness='unverified',signal_eligible=False)
        self.assertIn('0.830',v['option_metrics']('PCR').value)
        self.assertIn('UNVERIFIED',v['option_metrics']('PCR').value)
        self.assertIn('25,100',v['option_metrics']('OI').value)
        v['expiry'].value='2099-01-01'
        self.assertIn('not ready',v['option_metrics']('PCR').value)

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
            with self.assertRaises(FeedError):feed.history('NIFTY','5m','7d')
