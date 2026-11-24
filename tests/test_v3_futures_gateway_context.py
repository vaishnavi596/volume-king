"""Read-only futures quote context; tests use fake master and feed only."""
import unittest
from datetime import datetime,date,timedelta,timezone
from fastapi.testclient import TestClient
from backend.clone_v2_gateway import create_app
from backend.futures_context import select_verified_future,normalize_futures_ltp

SSK=b"offline-futures-unit-only-credential-123456"


class DummyDhan:
    def __init__(self):
        self.calls=[]
    def ltp(self,segment,sid):
        self.calls.append((segment,sid))
        return {"status":"success","data":{"NSE_FNO":{"12345":{"last_price":24500.5}}}}


class FuturesContextTests(unittest.TestCase):
    def setUp(self):
        self.expiry=datetime.now(timezone(timedelta(hours=5,minutes=30))).date()+timedelta(days=10)
        self.feed=DummyDhan()
        self.good={"source":"Dhan","master_verified":True,"instrument_type":"FUT",
                   "exchange_segment":"NSE_FNO","underlying":"RELIANCE",
                   "expiry":self.expiry.isoformat(),"security_id":"12345",
                   "contract":"RELIANCE FUT"}
    def client(self,master=True,rows=None):
        kw={"key_bytes":SSK,"market_registry":{"RELIANCE":("NSE_EQ",2885)},
            "market_feed_factory":lambda:self.feed}
        if master:
            kw["futures_master_factory"]=lambda: [self.good] if rows is None else rows
        return TestClient(create_app(**kw))
    def post(self,client,symbol="RELIANCE",expiry=None,secret=True):
        return client.post("/clone-v2/market/futures/context",
                           headers={"x-botking-key":SSK.decode() if secret else "invalid"},
                           json={"symbol":symbol,"expiry":(expiry or self.expiry).isoformat()})
    def test_contract_quote_only_context_not_trade_side(self):
        row=self.post(self.client())
        self.assertEqual(row.status_code,200)
        value=row.json()
        self.assertEqual(value["ltp"],24500.5)
        self.assertEqual(value["expiry"],self.expiry.isoformat())
        self.assertIsNone(value["direction"])
        self.assertFalse(value["direction_verified"])
        self.assertFalse(value["signal_eligible"])
        self.assertFalse(value["live_orders_enabled"])
        self.assertEqual(value["freshness"],"unverified")
        self.assertEqual(self.feed.calls,[("NSE_FNO","12345")])
    def test_missing_master_duplicate_wrong_contract_and_unauthorized_never_poll(self):
        self.assertEqual(self.post(self.client(master=False)).status_code,503)
        self.assertEqual(self.post(self.client(rows=[self.good,self.good])).status_code,422)
        self.assertEqual(self.post(self.client(rows=[dict(self.good,master_verified=False)])).status_code,422)
        self.assertEqual(self.post(self.client(),symbol="NIFTY").status_code,422)
        self.assertEqual(self.post(self.client(),expiry=date(2020,1,1)).status_code,422)
        self.assertEqual(self.post(self.client(),secret=False).status_code,403)
        self.assertEqual(self.feed.calls,[])
    def test_missing_invalid_quote_never_claims_futures_flow(self):
        mapped=select_verified_future([self.good],"RELIANCE",self.expiry)
        self.assertIsNotNone(mapped)
        for response in ({"status":"success","data":{}},
                         {"status":"success","data":{"NSE_FNO":{"12345":{"last_price":0}}}},
                         {"status":"success","data":{"NSE_FNO":{"12345":{"last_price":True}}}}):
            self.assertIsNone(normalize_futures_ltp(response,mapped))


if __name__=="__main__":
    unittest.main()
