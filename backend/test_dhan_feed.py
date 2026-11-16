"""Offline tests for the read-only Dhan quote adapter."""
import io
import json
import unittest
import urllib.error
from unittest.mock import patch
from dhan_feed import DhanFeed, DhanFeedError

class Response:
    def __init__(self, data):
        self.data = data
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, limit):
        return json.dumps(self.data).encode()

class DhanFeedTests(unittest.TestCase):
    def test_ltp_payload(self):
        def opener(request, timeout):
            self.assertEqual(timeout, 12)
            self.assertEqual(request.get_method(), "POST")
            self.assertEqual(json.loads(request.data), {"IDX_I": [13]})
            return Response({"status": "success", "data": {"IDX_I": {"13": {"last_price": 25030.35}}}})
        result = DhanFeed("client", "secret", opener=opener).ltp("IDX_I", 13)
        self.assertEqual(result["data"]["IDX_I"]["13"]["last_price"], 25030.35)

    def test_quote_one_per_second_across_multiple_adapter_instances(self):
        import dhan_feed
        clock=[100.0]
        sent=[]
        slept=[]
        def now():
            return clock[0]
        def sleep(seconds):
            self.assertGreater(seconds,0)
            slept.append(seconds)
            clock[0]+=seconds
        def opener(request, timeout):
            sent.append((clock[0],json.loads(request.data)))
            return Response({"status":"success","data":{}})
        with patch.object(dhan_feed.time,"monotonic",side_effect=now), \
             patch.object(dhan_feed.time,"sleep",side_effect=sleep), \
             patch.object(DhanFeed,"_quote_next_allowed",0.0), \
             patch.object(DhanFeed,"_retry_after",0.0):
            DhanFeed("client","test-key",opener=opener).ltp("IDX_I",13)
            DhanFeed("client","test-key",opener=opener).batch_ltp([("NSE_EQ",2885)])
        self.assertEqual(len(sent),2)
        self.assertEqual(sent[0][0],100.0)
        self.assertGreaterEqual(sent[1][0]-sent[0][0],1.05)
        self.assertEqual(len(slept),1)

    def test_cooldown_after_quote_wait_does_not_send_upstream(self):
        import dhan_feed
        clock=[100.0]
        sent=[]
        def now():return clock[0]
        def sleep(seconds):
            clock[0]+=seconds
        def opener(request, timeout):
            sent.append(request.full_url)
            return Response({"status":"success","data":{}})
        with patch.object(dhan_feed.time,"monotonic",side_effect=now), \
             patch.object(dhan_feed.time,"sleep",side_effect=sleep), \
             patch.object(DhanFeed,"_quote_next_allowed",101.05), \
             patch.object(DhanFeed,"_retry_after",102.0):
            with self.assertRaises(dhan_feed.DhanRateLimitError):
                DhanFeed("client","test-key",opener=opener).ltp("IDX_I",13)
        self.assertEqual(sent,[])

    def test_default_dhan_transport_blocks_redirect_and_environment_proxy(self):
        import dhan_feed
        from urllib.request import ProxyHandler
        opener=dhan_feed.direct_dhan_https_opener()
        self.assertTrue(any(isinstance(h,dhan_feed.RejectDhanRedirect)
                            for h in opener.handlers))
        proxy=[h for h in opener.handlers if isinstance(h,ProxyHandler)]
        self.assertEqual(len(proxy),1)
        self.assertEqual(proxy[0].proxies,{})
        self.assertIsNone(dhan_feed.RejectDhanRedirect().redirect_request(
            None,None,302,"Found",{},"https://attacker.invalid/capture"))
        with patch.object(dhan_feed,"direct_dhan_https_opener",return_value=opener) as built:
            adapter=DhanFeed("client","token-placeholder")
        built.assert_called_once_with()
        self.assertEqual(adapter._opener,opener.open)

    def test_invalid_security_id(self):
        with self.assertRaises(DhanFeedError):
            DhanFeed("client", "secret").ltp("IDX_I", "invalid")

    def test_auth_failure_has_no_secret(self):
        def opener(request, timeout):
            raise urllib.error.HTTPError(request.full_url, 401, "unauthorized", {}, None)
        with self.assertRaises(DhanFeedError) as caught:
            DhanFeed("client", "very-secret-token", opener=opener).ltp("IDX_I", 13)
        self.assertNotIn("very-secret-token", str(caught.exception))

if __name__ == "__main__":
    unittest.main()
