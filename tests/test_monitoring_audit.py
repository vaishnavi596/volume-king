import asyncio
import io
import json
import time
import unittest
from unittest.mock import patch
from test_audit import start
from feed_health import FeedHealth,safe_error,retry_delay
from market_feed import AngelFeed,SessionExpired

class MonitoringAuditTests(unittest.TestCase):
    def test_obsolete_response_does_not_override_new_health(self):
        health=FeedHealth(clock=lambda:100)
        first=health.begin('market');second=health.begin('market')
        self.assertFalse(health.finish('market',first,'UNAVAILABLE'))
        self.assertTrue(health.finish('market',second,'AVAILABLE',source='Yahoo',data_time=90))
        self.assertEqual(health.get('market')['last_success'],100)
    def test_errors_do_not_leak_exception_text(self):
        self.assertNotIn('PRIVATE',safe_error(RuntimeError('PRIVATE password')))
        self.assertEqual(safe_error(TimeoutError()),'Network timeout')
    def test_retry_backoff_is_bounded(self):
        self.assertEqual([retry_delay(i) for i in (1,2,3,4,5,50)],[30,60,120,240,300,300])
    def test_short_timeframes_have_strict_freshness(self):
        _,v=start({'scanner_live':False})
        self.assertEqual(v['timeframe_spec']('1m')['fresh_seconds'],150)
        self.assertEqual(v['timeframe_spec']('3m')['fresh_seconds'],390)
        self.assertEqual(v['timeframe_spec']('5m')['fresh_seconds'],630)
    def test_stale_one_minute_data_is_not_a_live_signal(self):
        _,v=start({'scanner_live':False})
        end=int(time.time())-600
        bars=[[end-(39-i)*60,100+i,103+i,99+i,102+i,100] for i in range(40)]
        result=v['analyze_current'](bars,None,'1m')
        self.assertEqual(result['bias'],'WAIT')
        self.assertIn('too old',result['reason'])
    def test_partial_super_five_updates_preserve_five_rows(self):
        _,v=start({'scanner_live':False,'source':'Yahoo Finance'})
        result={'bias':'BULLISH','score':90,'timestamp':time.time()-300,'source':'Yahoo Finance','reason':'trend','historical':False}
        v['publish_partial_ranking']({'TEST':result})
        self.assertEqual(len(v['top5_candidates']),5)
        self.assertEqual(v['top5_candidates'][0]['symbol'],'TEST')
        self.assertEqual(v['top5_candidates'][0]['bias'],'BULLISH')
    def test_fresh_neutral_is_not_mislabeled_as_old(self):
        _,v=start({'scanner_live':False})
        end=int(time.time()//300)*300-300
        bars=[[end-(39-i)*300,100,101,99,100,10] for i in range(40)]
        result=v['display_analysis']('TEST',{'bars':bars,'source':'Yahoo','cached':False})
        self.assertFalse(result['historical'])
    def test_lifecycle_pauses_and_resume_does_not_enable_trading(self):
        page,v=start({'scanner_live':False})
        v['protection_pending']['deadline']=1
        v['lifecycle_changed'](type('Event',(),{'state':'paused'})())
        self.assertFalse(v['app_active'][0]);self.assertFalse(v['protection_pending'])
        v['lifecycle_changed'](type('Event',(),{'state':'resumed'})())
        self.assertTrue(v['app_active'][0])
        self.assertTrue(any(fn==v['refresh_after_resume'] for fn,args in page.tasks))
        self.assertFalse(v['scan_live'].value)
    def test_session_expiry_clears_broker_credentials_in_memory(self):
        feed=AngelFeed();feed.key='test';feed.token='PRIVATE'
        class Response:
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def read(self):return b'{"status":false,"errorcode":"AG8002","data":null}'
        with patch('urllib.request.urlopen',return_value=Response()):
            with self.assertRaises(SessionExpired):feed.request('quote',{})
        self.assertFalse(feed.connected);self.assertFalse(feed.token)
    def test_market_health_and_explicit_broker_failure(self):
        _,v=start({'scanner_live':False,'source':'Broker API'})
        with self.assertRaises(Exception):v['get_market_data']('NIFTY')
        self.assertEqual(v['health'].get('market:Broker API:NIFTY:5m')['state'],'UNAVAILABLE')
        self.assertIn('last attempt',v['component_status']('market','NIFTY','5m'))
    def test_removed_capabilities_panel_keeps_execution_safety(self):
        _,v=start({'scanner_live':False})
        self.assertNotIn('execution_capabilities',v)
        self.assertIn('Live orders: OFF',v['help_status']('live auto trading'))
        self.assertEqual(v['mode'].value,'Paper')
    def test_option_help_uses_its_own_component_error(self):
        _,v=start({'scanner_live':False})
        key='options:'+v['chain_symbol'].value+':'+v['expiry'].value
        n=v['health'].begin(key);v['health'].finish(key,n,'UNAVAILABLE',error='Partial strike-window coverage')
        self.assertIn('Partial strike-window coverage',v['help_status']('OI Analysis'))
