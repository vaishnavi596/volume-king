"""127-B: bounded read-only Oracle snapshot recovery through fixed 51-equity Dhan batch."""
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from server_feed import ServerDhanReadOnly, FeedError, DHAN_VERIFIED_SYMBOLS, DHAN_VERIFIED_INDEX_SYMBOLS

EQUITIES=DHAN_VERIFIED_SYMBOLS-DHAN_VERIFIED_INDEX_SYMBOLS

class DirectEquityBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.feed=ServerDhanReadOnly()
        self.feed._origin="https://example.org"
        self.feed._pairing_key="unit-test-key"
        self.stale={"protocol":2,"source":"dhan","quotes":{},"unavailable":[],
            "age_seconds":None,"freshness":"stale_or_missing",
            "collection_status":"not_collected","error":"not_collected",
            "live_orders_enabled":False}
        self.batch={"source":"dhan","quotes":{s:float(100+i) for i,s in enumerate(sorted(EQUITIES))},
            "unavailable":[],"freshness":"unverified","live_orders_enabled":False}

    def test_one_direct_batch_on_stale_cache_then_throttle(self):
        calls=[]
        def fake(path, payload=None):
            calls.append((path,payload))
            return self.stale if path=="/v2/snapshot" else self.batch
        with patch.object(self.feed,"_call",side_effect=fake):
            first=self.feed.equity_quotes_with_bootstrap()
            self.assertEqual(set(first),EQUITIES)
            self.assertTrue(all(row["source"]=="Dhan" and
                row["freshness"]=="unverified" and row["live_verified"] is False and
                row["quote_timestamp"] is None for row in first.values()))
            with self.assertRaises(FeedError):
                self.feed.equity_quotes_with_bootstrap()
        self.assertEqual([p for p,_ in calls],
            ["/v2/snapshot","/dhan/ltp-batch","/v2/snapshot"])
        self.assertIsNone(calls[0][1])
        self.assertEqual(calls[1][1],{})
        self.feed.disconnect()
        self.assertEqual(self.feed._direct_equity_last_attempt,0.0)

    def test_valid_cache_never_calls_provider(self):
        snapshot=dict(self.stale,quotes={"RELIANCE":1339.7},age_seconds=10,
            freshness="unverified",collection_status="recently_collected",error=None)
        with patch.object(self.feed,"_call",return_value=snapshot) as call:
            self.assertEqual(self.feed.equity_quotes_with_bootstrap()["RELIANCE"]["price"],1339.7)
        call.assert_called_once_with("/v2/snapshot")

    def test_invalid_provider_contract_never_publishes_prices(self):
        for change in ({"live_orders_enabled":True},{"quotes":{"RELIANCE":0}},
                       {"source":"yahoo"},{"unavailable":["NIFTY"]},
                       {"quotes":{"RELIANCE":1339.7},"unavailable":[]}):
            with self.subTest(change=change):
                feed=ServerDhanReadOnly()
                feed._origin="https://example.org";feed._pairing_key="test"
                invalid=dict(self.batch,**change)
                with patch.object(feed,"_call",side_effect=[self.stale,invalid]):
                    with self.assertRaises(FeedError):
                        feed.equity_quotes_with_bootstrap()

    def test_auth_network_and_rate_limit_fail_closed_no_direct_call(self):
        for message in ("Dhan server disconnected; reconnect in Settings",
                        "Dhan API rate limited (HTTP 429); wait before retry",
                        "Dhan batch network request failed (HTTP 502)"):
            with self.subTest(message=message):
                with patch.object(self.feed,"batch_quotes",side_effect=FeedError(message)),\
                     patch.object(self.feed,"_call") as call:
                    with self.assertRaises(FeedError):
                        self.feed.equity_quotes_with_bootstrap()
                call.assert_not_called()
        with patch.object(self.feed,"batch_quotes",side_effect=FeedError(
                "Oracle Dhan snapshot missing, stale or invalid")),\
             patch.object(self.feed,"cooldown_remaining",return_value=30),\
             patch.object(self.feed,"_call") as call:
            with self.assertRaises(FeedError):
                self.feed.equity_quotes_with_bootstrap()
        call.assert_not_called()

    def test_app_login_and_regular_poll_share_same_bounded_method(self):
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text()
        self.assertEqual(source.count(
            "await asyncio.to_thread(dhan_feed.equity_quotes_with_bootstrap)"),2)
        self.assertNotIn("await asyncio.to_thread(dhan_feed.batch_quotes)",source)

if __name__=="__main__":
    unittest.main()
