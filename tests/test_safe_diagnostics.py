import io
import json
import unittest
import urllib.error
from unittest.mock import patch
from market_feed import AngelFeed,FeedError,SessionExpired
from backend.server import log_data_failure

class SafeDiagnosticsTests(unittest.TestCase):
    def feed(self):
        f=AngelFeed();f.key='PRIVATE_API';f.token='PRIVATE_JWT';return f
    def test_broker_http_status_logged_without_secret_or_body(self):
        f=self.feed()
        e=urllib.error.HTTPError('https://private.example',403,'PRIVATE_BODY',{},None)
        with patch('urllib.request.urlopen',side_effect=e),patch('market_feed.time.sleep'),self.assertLogs('botking.diagnostics',level='WARNING') as log:
            with self.assertRaises(SessionExpired):f.request('candles',{'client':'PRIVATE_CLIENT'})
        text=' '.join(log.output)
        self.assertIn('operation=candles http=403',text)
        for secret in ('PRIVATE_API','PRIVATE_JWT','PRIVATE_BODY','PRIVATE_CLIENT','private.example'):self.assertNotIn(secret,text)
        self.assertFalse(f.connected)  # Authentication enforcement is unchanged.
    def test_only_expected_broker_code_pattern_is_logged(self):
        for code,expected in [('AG8001','AG8001'),('PRIVATE_SECRET','UNCLASSIFIED')]:
            f=self.feed()
            class Response(io.BytesIO):
                def __enter__(self):return self
                def __exit__(self,*args):self.close()
            response=Response(json.dumps({'status':False,'errorcode':code,'message':'PRIVATE_BODY'}).encode())
            with patch('urllib.request.urlopen',return_value=response),patch('market_feed.time.sleep'),self.assertLogs('botking.diagnostics',level='WARNING') as log:
                with self.assertRaises(FeedError):f.request('search',{})
            text=' '.join(log.output)
            self.assertIn('error_code='+expected,text);self.assertNotIn('PRIVATE',text)
    def test_gateway_reason_is_allowlisted_not_exception_text(self):
        with self.assertLogs('botking.diagnostics',level='WARNING') as log:
            log_data_failure('history',RuntimeError('PRIVATE_JWT'))
            log_data_failure('history',FeedError('Exact broker symbol unavailable'))
        text=' '.join(log.output)
        self.assertNotIn('PRIVATE',text);self.assertIn('reason=symbol_resolution',text)
