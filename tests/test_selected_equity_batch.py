"""Bounded selected Dhan equities: one broker call, zero fabricated prices."""
import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.server import create_app
from backend.dhan_feed import DhanRateLimitError
from market_feed import FeedError
from server_feed import ServerDhanReadOnly


class SelectedEquityBatchTests(unittest.TestCase):
    def setUp(self):
        self.key = "k"*40
        self.client = TestClient(create_app(pairing_key=self.key))
        self.headers = {"X-BotKing-Key": self.key}

    def test_auth_unknown_and_large_selection_fail_before_provider(self):
        with patch("backend.server.DhanFeed.batch_ltp",side_effect=AssertionError("provider called")):
            self.assertEqual(self.client.post("/dhan/selected-ltp-batch",
                json={"symbols":["RELIANCE"]}).status_code,403)
            for names in (["UNKNOWN"], ["RELIANCE"]*2, ["RELIANCE"]*71,
                          [], ["reliance"], ["NIFTY"]):
                with self.subTest(names=names[:3]):
                    self.assertEqual(self.client.post("/dhan/selected-ltp-batch",
                        headers=self.headers,json={"symbols":names}).status_code,422)

    def test_one_provider_batch_and_partial_unavailable(self):
        with patch.dict(os.environ,{"DHAN_CLIENT_ID":"test-client"}):
            with patch("pathlib.Path.read_text",return_value="test-token"):
                with patch("backend.server.DhanFeed.batch_ltp",return_value={
                    "status":"success","data":{"NSE_EQ":{"2885":{"last_price":1288.0}}}
                }) as feed:
                    res=self.client.post("/dhan/selected-ltp-batch",headers=self.headers,
                        json={"symbols":["RELIANCE","HDFCBANK"]})
        self.assertEqual(res.status_code,200)
        self.assertEqual(res.json()["quotes"],{"RELIANCE":1288.0})
        self.assertEqual(res.json()["unavailable"],["HDFCBANK"])
        self.assertFalse(res.json()["live_orders_enabled"])
        feed.assert_called_once_with([("NSE_EQ",2885),("NSE_EQ",1333)])

    def test_adapter_rejects_unrequested_or_invalid_prices(self):
        a=ServerDhanReadOnly()
        a._origin="https://example.org";a._pairing_key="test"
        good={"source":"dhan","live_orders_enabled":False,
              "freshness":"unverified","quote_timestamp":None,
              "quotes":{"RELIANCE":1288.0},"unavailable":["HDFCBANK"]}
        with patch.object(a,"_call",return_value=good) as call:
            out=a.selected_equity_quotes(["RELIANCE","HDFCBANK"])
        self.assertEqual(out["RELIANCE"]["price"],1288.0)
        self.assertFalse(out["RELIANCE"]["live_verified"])
        call.assert_called_once_with("/dhan/selected-ltp-batch",
                                     {"symbols":["RELIANCE","HDFCBANK"]})
        for payload in ({**good,"quotes":{"RELIANCE":0}},
                        {**good,"unavailable":[]},
                        {**good,"quotes":{"NIFTY":100.0}}):
            with patch.object(a,"_call",return_value=payload):
                with self.assertRaises(FeedError):
                    a.selected_equity_quotes(["RELIANCE","HDFCBANK"])


if __name__=="__main__":
    unittest.main()
