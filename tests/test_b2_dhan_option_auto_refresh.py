"""B2: Dhan-only broker-listed expiry and auto-refresh integration regressions."""
import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.server import create_app
from backend.dhan_feed import DhanFeed, DhanFeedError


class DhanMultiUnderlyingOptionsTests(unittest.TestCase):
    def setUp(self):
        self.key = "k" * 40
        self.http = TestClient(create_app(pairing_key=self.key))
        self.headers = {"X-BotKing-Key": self.key}

    def test_expiry_endpoint_never_returns_guessed_dates(self):
        with patch.dict(os.environ, {"DHAN_CLIENT_ID": "test"}):
            with patch("pathlib.Path.read_text", return_value="test-token"):
                with patch("backend.server.DhanFeed.option_expiries",
                           return_value=["2099-12-31"]) as request:
                    result = self.http.post("/dhan/option-expiries",
                        json={"symbol":"HDFCBANK"},headers=self.headers)
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.json()["expiries"],["2099-12-31"])
        self.assertFalse(result.json()["live_orders_enabled"])
        request.assert_called_once_with("NSE_EQ",1333)

    def test_banknifty_uses_mapped_index_underlying(self):
        with patch.dict(os.environ, {"DHAN_CLIENT_ID": "test"}):
            with patch("pathlib.Path.read_text", return_value="test-token"):
                with patch("backend.server.DhanFeed.option_expiries",
                           return_value=["2099-12-31"]) as request:
                    result=self.http.post("/dhan/option-expiries",
                        json={"symbol":"BANKNIFTY"},headers=self.headers)
        self.assertEqual(result.status_code,200)
        request.assert_called_once_with("IDX_I",25)

    def test_no_entitlement_does_not_fabricate_list(self):
        with patch.dict(os.environ, {"DHAN_CLIENT_ID": "test"}):
            with patch("pathlib.Path.read_text", return_value="test-token"):
                with patch("backend.server.DhanFeed.option_expiries",
                           return_value=[]):
                    result=self.http.post("/dhan/option-expiries",
                        json={"symbol":"RELIANCE"},headers=self.headers)
        self.assertEqual(result.status_code,422)
        self.assertNotIn("expiries",result.json())

    def test_expiry_auth_and_unknown_underlying_fail_closed(self):
        self.assertEqual(self.http.post("/dhan/option-expiries",
            json={"symbol":"NIFTY"}).status_code,403)
        self.assertEqual(self.http.post("/dhan/option-expiries",
            json={"symbol":"MADEUP"},headers=self.headers).status_code,422)

    def test_provider_expiry_api_is_paced_and_read_only(self):
        feed=DhanFeed("client","token")
        with patch.object(DhanFeed,"_option_next_allowed",0.0):
            with patch.object(feed,"_post",return_value={"status":"success",
                                    "data":["2099-12-31","2099-12-31"]}) as call:
                self.assertEqual(feed.option_expiries("NSE_EQ",2885),["2099-12-31"])
                call.assert_called_once_with("/optionchain/expirylist",{
                    "UnderlyingScrip":2885,"UnderlyingSeg":"NSE_EQ"})

    def test_mobile_has_auto_refresh_for_all_mapped_option_symbols(self):
        from pathlib import Path
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text()
        auto=source.split("    async def option_poll():",1)[1].split(
            "    def selected_option_rows():",1)[0]
        self.assertIn('chain_symbol.value in DHAN_VERIFIED_SYMBOLS',auto)
        self.assertNotIn('chain_symbol.value=="NIFTY"',auto)
        self.assertIn("await refresh_selected_options()",auto)
        self.assertIn("option_refresh_pending[0]",source)
        self.assertNotIn('ft.ElevatedButton("Refresh Dhan Option Chain"',source)
        self.assertNotIn('ft.ElevatedButton("Refresh selected data"',source)


if __name__=="__main__":
    unittest.main()
