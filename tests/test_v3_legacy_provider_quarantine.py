"""V3 retired provider deep scan: no old Angel/Yahoo transport in app.

The original V1 backend and archived regression fixtures are deliberately not
modified. Fake methods must never send HTTP, even via injected callbacks.
"""
from pathlib import Path
from unittest.mock import patch
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
MAIN=(ROOT/"src/main.py").read_text(encoding="utf-8")
QUARANTINE=(ROOT/"src/v3_disabled_legacy_broker.py").read_text(encoding="utf-8")
sys.path.insert(0,str(ROOT/"src"))
from v3_disabled_legacy_broker import V3DisabledLegacyBroker


class V3LegacyProviderQuarantine(unittest.TestCase):
    def test_legacy_object_cannot_contact_broker(self):
        adapter=V3DisabledLegacyBroker()
        with patch("urllib.request.urlopen",side_effect=AssertionError("network used")) as network:
            self.assertFalse(adapter.connected)
            for method in ("connect","history","option_history","quote",
                           "request","expiries","master","option_chain"):
                with self.subTest(method=method):
                    with self.assertRaisesRegex(RuntimeError,"retired broker transport disabled"):
                        getattr(adapter,method)("not-real-credentials")
            adapter.revoke()
            adapter.disconnect()
            self.assertFalse(adapter.connected)
            self.assertGreaterEqual(adapter.epoch,2)
            network.assert_not_called()

    def test_v3_main_does_not_instantiate_angel_network_adapter(self):
        self.assertIn("angel_feed=V3DisabledLegacyBroker()",MAIN)
        self.assertNotIn("ServerAngelFeed()",MAIN)
        self.assertNotIn("from server_feed import ServerAngelFeed",MAIN)
        self.assertNotIn("angel_feed.connect(",MAIN)
        self.assertNotIn("angel_feed.history(",MAIN)
        self.assertNotIn("angel_feed.option_history(",MAIN)
        self.assertNotIn("broker_fields={\n        \"Angel One\"",MAIN)

    def test_unreachable_legacy_candle_network_branches_removed(self):
        block=MAIN.split("    def fetch_market_data_uncached(",1)[1].split(
            "    def timeframe_spec(",1)[0]
        self.assertIn('if selected!="Dhan":',block)
        self.assertIn('if selected=="Dhan":',block)
        self.assertNotIn('if selected=="Yahoo Finance":',block)
        self.assertNotIn('elif selected=="Broker API"',block)
        self.assertNotIn("angel_feed.history",block)
        self.assertNotIn("get_yahoo(ticker",block)
        self.assertNotIn("symbols_yahoo=",MAIN)

    def test_legacy_login_and_option_history_callbacks_are_inert(self):
        old=MAIN.split("    async def connect_angel():",1)[1].split(
            "    async def start_dhan_authorization():",1)[0]
        self.assertNotIn("await asyncio.to_thread",old)
        self.assertNotIn("urllib.request",old)
        self.assertIn("Only Dhan via Clone SSK",old)
        option=MAIN.split("    async def load_option_history():",1)[1].split(
            "    def option_chart_panel():",1)[0]
        self.assertIn("no broker request sent",option)
        self.assertNotIn("angel_feed.",option)
        self.assertNotIn("market_store.put",option)

    def test_background_lanes_accept_only_dhan_selection(self):
        self.assertNotIn('prefs.get("source") in ("Yahoo Finance","Broker API","Dhan")',MAIN)
        self.assertNotIn('prefs.get("source") not in ("Yahoo Finance","Broker API","Dhan")',MAIN)
        self.assertIn('prefs.get("source")=="Dhan"',MAIN)
        self.assertIn('broker_fields={"Dhan":[]}',MAIN)


if __name__=="__main__":
    unittest.main()
