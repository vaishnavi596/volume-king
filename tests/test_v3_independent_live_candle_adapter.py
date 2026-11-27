"""Independent C adapter: raw completed bars, no provider IO."""
import unittest
from datetime import datetime, timezone, timedelta
from five_engine import verified_candle_evidence, scanner_snapshot_with_candle

class IndependentCandleAdapterTest(unittest.TestCase):
    def fixture(self):
        start=datetime(2026,11,23,10,0,tzinfo=timezone(timedelta(hours=5,minutes=30))).timestamp()
        bars=[[start+i*300,100,103,99,102,50] for i in range(8)]
        history=dict(symbol="NIFTY",source="Dhan",_scanner_timeframe="5m",
                     live_verified=True,historical=False,freshness="verified_live",bars=bars)
        return history,start+8*300
    def test_verified_completed_raw_bodies(self):
        h,now=self.fixture()
        c=verified_candle_evidence(h,"5m",now=now,symbol="NIFTY")
        self.assertTrue(c.eligible)
        self.assertEqual((c.bullish,c.bearish),(100,0))
    def test_reject_unverified_wrong_frame_symbol_and_stale(self):
        h,now=self.fixture()
        for change in (dict(historical=True),dict(live_verified=False),
                       dict(symbol="TCS"),dict(_scanner_timeframe="1m"),dict(cached=True)):
            self.assertFalse(verified_candle_evidence(dict(h,**change),"5m",now=now,symbol="NIFTY").eligible)
        self.assertFalse(verified_candle_evidence(h,"5m",now=now+601,symbol="NIFTY").eligible)
    def test_one_minute_window_matches_live_bridge_tolerance(self):
        start=datetime(2026,11,23,10,0,tzinfo=timezone(timedelta(hours=5,minutes=30))).timestamp()
        bars=[[start+i*60,100,103,99,102,50] for i in range(10)]
        h=dict(symbol="NIFTY",source="Dhan",_scanner_timeframe="1m",
               live_verified=True,historical=False,freshness="exchange_verified",bars=bars)
        close=start+10*60
        self.assertTrue(verified_candle_evidence(h,"1m",now=close+85,symbol="NIFTY").eligible)
        self.assertFalse(verified_candle_evidence(h,"1m",now=close+95,symbol="NIFTY").eligible)
    def test_join_does_not_duplicate_technical_vote_or_invent_quorum(self):
        h,now=self.fixture()
        scan=dict(symbol="NIFTY",timeframe="5m",source="Dhan",live_verified=True,
                  historical=False,freshness="verified_live",timestamp=now-300,
                  votes=[dict(name=n,vote=-1) for n in ("Supertrend","EMA 9/21","RSI 14")])
        snap=scanner_snapshot_with_candle(scan,h,symbol="NIFTY",timeframe="5m",now=now)
        self.assertEqual(snap["engines"][0].bearish,100)
        self.assertEqual(snap["engines"][1].bullish,100)
        self.assertEqual(snap["combined"]["coverage"],2)
        self.assertEqual(snap["combined"]["state"],"WAIT")
        scan["timestamp"]-=300
        self.assertFalse(scanner_snapshot_with_candle(scan,h,symbol="NIFTY",timeframe="5m",now=now)["engines"][1].eligible)

    def test_gateway_historical_shape_cannot_vote_live(self):
        h,now=self.fixture()
        h.update(historical=True,live_verified=False,freshness='historical_unverified',
                 candle_transport_integrity='SHA256_MATCH',
                 candle_raw_provider_provenance='UNVERIFIED')
        self.assertFalse(verified_candle_evidence(h,'5m',now=now,symbol='NIFTY').eligible)

    def test_historical_suffix_cannot_supply_live_revision(self):
        h,now=self.fixture()
        end=datetime(2026,11,23,15,25,tzinfo=timezone(timedelta(hours=5,minutes=30))).timestamp()
        h['bars']=[[end-(29-i)*300,100,103,99,102,50] for i in range(30)]
        h['bars'].append([end+300,100,103,99,102,50])
        self.assertFalse(verified_candle_evidence(h,'5m',now=end+600,symbol='NIFTY').eligible)
