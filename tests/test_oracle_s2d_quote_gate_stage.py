"""Staging-only S2D quote gate: production customs remain and no live API."""
import ast
import unittest
from scripts.oracle_s2d_quote_gate_stage import make_stage

SOURCE = '''import json
import threading
import time
import urllib.request

class DhanRateLimitError(Exception): pass
class DhanFeed:
    _rate_lock = threading.Lock()
    _retry_after = 0.0
    _historical_retry_after = 0.0
    _option_retry_after = 0.0
    def __init__(self, opener):
        self._opener = opener
    def _post(self, endpoint, payload):
        with self._rate_lock:
            cooldown = (DhanFeed._historical_retry_after if endpoint in ("/charts/intraday", "/charts/historical")
                        else DhanFeed._option_retry_after if endpoint in ("/optionchain", "/optionchain/expirylist")
                        else DhanFeed._retry_after)
            if time.monotonic() < cooldown:
                raise DhanRateLimitError("Dhan rate limit cooldown active")
        request = urllib.request.Request("https://api.dhan.co/v2" + endpoint)
        try:
            with self._opener(request, timeout=12) as response:
                raw = response.read(2_000_001)
            return raw
        except ValueError:
            raise
'''

class OracleS2DQuoteGateTests(unittest.TestCase):
    def test_preserves_custom_cooldowns_and_adds_quote_gate(self):
        staged=make_stage(SOURCE)
        self.assertIn("QUOTE_MIN_INTERVAL_SECONDS = 1.05",staged)
        self.assertIn("DhanFeed._historical_retry_after",staged)
        self.assertIn("DhanFeed._option_retry_after",staged)
        self.assertEqual(staged.count("with self._opener(request, timeout=12)"),1)
        ast.parse(staged)
        self.assertEqual(make_stage.__name__,"make_stage")
        with self.assertRaisesRegex(ValueError,"already present"):
            make_stage(staged)

    def test_fail_closed_on_unexpected_source(self):
        for bad in [
            SOURCE.replace("class DhanFeed:", "class OtherFeed:"),
            SOURCE.replace("with self._opener(request, timeout=12)", "with opener(request, timeout=12)"),
            SOURCE.replace("    _historical_retry_after = 0.0\n", "").replace(
                "DhanFeed._historical_retry_after","DhanFeed._unknown"),
            SOURCE.replace("    _retry_after = 0.0", "    _quote_lock = threading.Lock()"),
        ]:
            with self.subTest(bad=bad[:90]), self.assertRaises(ValueError):
                make_stage(bad)

    def test_staged_quote_gate_serializes_across_instances(self):
        # Use a fake clock and opener: verify direct quote gap without network.
        import threading
        from unittest.mock import patch
        staged=make_stage(SOURCE)
        ns={}
        exec(compile(staged,"<staged>","exec"),ns)
        feed=ns["DhanFeed"]
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def read(self,n): return b"{}"
        starts=[]
        def opener(*args,**kwargs):
            starts.append(fake_clock[0])
            return Response()
        fake_clock=[10.]
        def monotonic(): return fake_clock[0]
        def sleep(s): fake_clock[0]+=s
        with patch.object(ns["time"],"monotonic",side_effect=monotonic), patch.object(ns["time"],"sleep",side_effect=sleep):
            feed(opener)._post("/marketfeed/ltp",{})
            feed(opener)._post("/marketfeed/ltp",{})
            feed(opener)._post("/charts/intraday",{})
        self.assertEqual(len(starts),3)
        self.assertGreaterEqual(starts[1]-starts[0],1.05)
        self.assertEqual(starts[2],starts[1])

if __name__=="__main__":
    unittest.main()
