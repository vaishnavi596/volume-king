"""Offline clone-phone Futures context integration, no network or trading."""
import pathlib
import sys
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from clone_v2_gateway import CloneDhanReadOnly,FeedError


class FakeGateway:
    connected=True
    def __init__(self,override=None):
        self.calls=[]
        self.override=override or {}
    def post_market(self,route,selection):
        self.calls.append((route,selection))
        return dict(source="dhan",symbol="RELIANCE",underlying="RELIANCE",
                    expiry="2026-12-31",contract="RELIANCE DEC FUT",
                    exchange_segment="NSE_FNO",mapping_verified=True,
                    ltp=1300.25,freshness="unverified",
                    direction_verified=False,signal_eligible=False,
                    direction=None,live_orders_enabled=False,**self.override)


class FuturesPhoneContextTests(unittest.TestCase):
    def test_authentic_mapped_quote_stays_context_not_vote(self):
        gateway=FakeGateway()
        result=CloneDhanReadOnly(gateway).futures_context("RELIANCE","2026-12-31")
        self.assertEqual(gateway.calls,[("futures/context",{
            "symbol":"RELIANCE","expiry":"2026-12-31"})])
        self.assertFalse(result["direction_verified"])
        self.assertIsNone(result["direction"])
        self.assertEqual(result["freshness"],"unverified")
        self.assertFalse(result["signal_eligible"])
        self.assertFalse(result["live_orders_enabled"])

    def test_bad_expiry_never_sends_provider_request(self):
        gateway=FakeGateway()
        for expiry in ("2026-02-30","unknown",True,"2026-12-31T00:00:00"):
            with self.subTest(expiry=expiry):
                with self.assertRaises(FeedError):
                    CloneDhanReadOnly(gateway).futures_context("RELIANCE",expiry)
        self.assertEqual(gateway.calls,[])

    def test_bad_evidence_can_never_be_futures_vote(self):
        good=dict(source="dhan",symbol="RELIANCE",underlying="RELIANCE",
                  expiry="2026-12-31",contract="RELIANCE DEC FUT",
                  exchange_segment="NSE_FNO",mapping_verified=True,ltp=1300.25,
                  freshness="unverified",direction_verified=False,
                  signal_eligible=False,direction=None,live_orders_enabled=False)
        for patch in ({"underlying":"NIFTY"},{"expiry":"2027-01-28"},
                      {"mapping_verified":False},{"source":"Yahoo"},
                      {"ltp":0},{"ltp":True},{"ltp":float("nan")},
                      {"direction":"BULLISH"},{"direction_verified":True},
                      {"signal_eligible":True},{"freshness":"verified_live"},
                      {"live_orders_enabled":True}):
            gateway=FakeGateway()
            gateway.post_market=lambda route,selection,patch=patch:dict(good,**patch)
            with self.subTest(patch=patch):
                with self.assertRaises(FeedError):
                    CloneDhanReadOnly(gateway).futures_context("RELIANCE","2026-12-31")


if __name__=="__main__":
    unittest.main()
