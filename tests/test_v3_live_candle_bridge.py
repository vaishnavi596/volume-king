import unittest
from datetime import datetime
from v3_equity_session_calendar import IST
from v3_live_candle_bridge import completed_live_history
class LiveCandleBridgeTests(unittest.TestCase):
    def test_current_exact_completed_and_fail_closed(self):
        now=datetime(2026,11,26,11,4,20,tzinfo=IST).timestamp()
        start=now-200
        bars=[[start+i*60,100,102,99,101,10] for i in range(4)]
        q={"source":"Dhan","quote_timestamp":now-5,"timestamp_origin":"DHAN_QUOTE_LAST_TRADE_TIME"}
        r={"source":"dhan","symbol":"NIFTY","interval":"1m","normalized_transport_integrity":"SHA256_MATCH","candle_origin":"DHAN_INTRADAY_TIMESTAMP"}
        def check(r=r,q=q,now=now):
            return completed_live_history(r,bars,q,symbol="NIFTY",timeframe="1m",now=now)
        self.assertEqual(check(),bars[:3])
        self.assertIsNone(check(q=dict(q,cached=True)))
        self.assertIsNone(check(q=dict(q,quote_timestamp=now-100)))
        self.assertIsNone(check(r=dict(r,candle_origin=None)))
        self.assertIsNone(check(r=dict(r,symbol="SENSEX")))
        self.assertIsNone(check(now=now+86400))
