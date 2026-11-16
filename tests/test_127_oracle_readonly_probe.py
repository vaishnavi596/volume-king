"""127-B/D read-only Oracle probe contract tests; no external requests."""
import unittest
from scripts.check_127_oracle_readonly import probe, request, origin_checked, RejectRedirect


class ReadOnlyOracleProbeTests(unittest.TestCase):
    def test_bounded_equity_index_and_stock_option_probe(self):
        calls, pauses = [], []
        def fake(origin,key,path,payload=None):
            calls.append((path,payload))
            ok={"http":200,"error":None}
            if path=="/dhan/status":
                return ok,{"authenticated":True,"market_data_configured":True}
            if path=="/v2/snapshot":
                return ok,{"source":"dhan","freshness":"unverified",
                           "age_seconds":80,"quotes":{f"STOCK{i}":100 for i in range(51)}}
            if path=="/dhan/index-ltp-batch":
                return ok,{"source":"dhan","freshness":"unverified",
                           "quotes":dict.fromkeys(("NIFTY","BANKNIFTY","SENSEX"),{}),
                           "unavailable":[]}
            if path=="/dhan/selected-ltp-batch":
                return ok,{"source":"dhan","quotes":{"RELIANCE":{},"HDFCBANK":{}}}
            if path=="/dhan/option-expiries":
                return ok,{"expiries":["2099-12-31"]}
            if path=="/dhan/option-chain":
                return ok,{"source":"dhan","symbol":payload["symbol"],
                           "expiry":"2099-12-31","freshness":"unverified",
                           "signal_eligible":False,"pcr":0.9,"max_pain":1500,
                           "atm_window":{"rows":[{}]*7}}
            raise AssertionError("Unexpected endpoint")
        out=probe("https://example.org","secret-not-printed",
                  selected=("RELIANCE","HDFCBANK"),
                  requester=fake,pause=pauses.append)
        self.assertEqual(out["snapshot"]["count"],51)
        self.assertEqual(out["indices"]["count"],3)
        self.assertEqual(out["selected"]["count"],2)
        for symbol in ("RELIANCE","HDFCBANK"):
            self.assertEqual(out["options"][symbol]["atm_strike_count"],7)
            self.assertTrue(out["options"][symbol]["pcr_available"])
        self.assertEqual(pauses,[3.5,3.5,3.5])
        self.assertEqual(len(calls),8)
        self.assertTrue(all(path in (
            "/dhan/status","/v2/snapshot","/dhan/index-ltp-batch",
            "/dhan/selected-ltp-batch","/dhan/option-expiries","/dhan/option-chain")
            for path,_ in calls))
        self.assertFalse(out["live_orders_enabled"])

    def test_unlisted_option_does_not_guess_expiry_or_retry(self):
        calls=[]
        def fake(origin,key,path,payload=None):
            calls.append(path)
            if path=="/dhan/status":
                return {"http":200,"error":None},{"authenticated":True,"market_data_configured":True}
            if path=="/dhan/option-expiries":
                return {"http":422,"error":"symbol_or_expiry_not_listed"},None
            return {"http":503,"error":"unavailable"},None
        out=probe("https://example.org","secret",option_symbols=("RELIANCE",),
                  requester=fake,pause=lambda x:None)
        self.assertEqual(out["options"]["RELIANCE"]["chain_error"],"no_listed_expiry")
        self.assertNotIn("/dhan/option-chain",calls)

    def test_option_429_stops_later_symbol_requests(self):
        calls=[]
        def fake(origin,key,path,payload=None):
            calls.append((path,payload))
            if path=="/dhan/status":
                return {"http":200,"error":None},{"authenticated":True,"market_data_configured":True}
            if path=="/dhan/option-expiries":
                return {"http":429,"error":"rate_limited"},None
            return {"http":503,"error":"unavailable"},None
        out=probe("https://example.org","x"*40,
                  option_symbols=("RELIANCE","HDFCBANK"),requester=fake,pause=lambda _:None)
        self.assertEqual(out["options_status"],"rate_limited_remaining_skipped")
        self.assertIn("RELIANCE",out["options"])
        self.assertNotIn("HDFCBANK",out["options"])
        self.assertEqual([p for p,_ in calls].count("/dhan/option-expiries"),1)
        self.assertNotIn("/dhan/option-chain",[p for p,_ in calls])

    def test_index_429_stops_option_calls_even_with_auth(self):
        calls=[]
        def fake(origin,key,path,payload=None):
            calls.append(path)
            if path=="/dhan/status":
                return {"http":200,"error":None},{"authenticated":True,"market_data_configured":True}
            if path=="/dhan/index-ltp-batch":
                return {"http":429,"error":"rate_limited"},None
            return {"http":503,"error":"unavailable"},None
        result=probe("https://example.org","x"*40,
                     requester=fake,pause=lambda _:None)
        self.assertEqual(result["options_status"],"skipped_account_rate_limit")
        self.assertNotIn("/dhan/option-expiries",calls)
        self.assertNotIn("/dhan/option-chain",calls)

    def test_no_auth_skips_all_option_requests_and_redirect_denied(self):
        calls=[]
        def fake(origin,key,path,payload=None):
            calls.append(path)
            return {"http":403,"error":"pairing_rejected"},None
        out=probe("https://example.org","x"*40,
                  requester=fake,pause=lambda _:None)
        self.assertEqual(out["options_status"],"skipped_no_authenticated_market_data")
        self.assertNotIn("/dhan/option-expiries",calls)
        self.assertIsNone(RejectRedirect().redirect_request(
            None,None,302,"Found",{},"https://untrusted.example/secret"))

    def test_non_readonly_routes_rejected_before_network(self):
        self.assertEqual(origin_checked("https://example.org"),"https://example.org")
        with self.assertRaises(ValueError):
            origin_checked("http://example.org")
        with self.assertRaises(ValueError):
            request("https://example.org","x"*40,"/v1/orders",{})
        with self.assertRaises(ValueError):
            probe("https://example.org","x",option_symbols=("MADEUP",),
                  requester=lambda *args,**kwargs:({"http":422,"error":"blocked"},None),
                  pause=lambda _:None)


if __name__=="__main__":
    unittest.main()
