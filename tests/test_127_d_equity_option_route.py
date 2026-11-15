"""127-D: mocked Oracle route contract for mapped stock option underlyings.

These checks do NOT verify Dhan entitlement or an actual listed expiry.
"""
import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.server import create_app


class EquityOptionRoute127(unittest.TestCase):
    def setUp(self):
        self.key="k"*40
        self.api=TestClient(create_app(pairing_key=self.key))
        self.headers={"X-BotKing-Key":self.key}
        self.payload={"symbol":"RELIANCE","expiry":"2099-12-31"}

    def test_stock_chain_uses_cash_underlying_security_id(self):
        fake={"status":"success","data":{"oc":{
            "1500":{"ce":{"oi":100},"pe":{"oi":50}},
            "1510":{"ce":{"oi":50},"pe":{"oi":100}}
        }}}
        for symbol,sid in (("RELIANCE",2885),("HDFCBANK",1333)):
            with self.subTest(symbol=symbol):
                with patch.dict(os.environ,{"DHAN_CLIENT_ID":"test-client"}):
                    with patch("pathlib.Path.read_text",return_value="test-token"):
                        with patch("backend.server.DhanFeed.option_chain",return_value=fake) as call:
                            resp=self.api.post("/dhan/option-chain",
                                json={"symbol":symbol,"expiry":"2099-12-31"},
                                headers=self.headers)
                self.assertEqual(resp.status_code,200,resp.text)
                data=resp.json()
                self.assertEqual(data["symbol"],symbol)
                self.assertEqual(data["source"],"dhan")
                self.assertEqual(data["freshness"],"unverified")
                self.assertFalse(data["signal_eligible"])
                self.assertFalse(data["live_orders_enabled"])
                self.assertEqual(data["atm_window_status"],"underlying_spot_unavailable")
                call.assert_called_once_with("NSE_EQ",sid,"2099-12-31")

    def test_reliance_not_entitled_returns_error_no_fake_premium(self):
        from backend.dhan_feed import DhanFeedError
        with patch.dict(os.environ,{"DHAN_CLIENT_ID":"test-client"}):
            with patch("pathlib.Path.read_text",return_value="test-token"):
                with patch("backend.server.DhanFeed.option_chain",side_effect=DhanFeedError("blocked")):
                    resp=self.api.post("/dhan/option-chain",json=self.payload,headers=self.headers)
        self.assertEqual(resp.status_code,502)
        self.assertNotIn("pcr",resp.json())
        self.assertNotIn("atm_window",resp.json())


if __name__=="__main__":
    unittest.main()
