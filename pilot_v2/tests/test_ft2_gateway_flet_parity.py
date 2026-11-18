"""FT-2 existing read-only gateway schema ↔ Flet quote consumer parity.

Synthetic, no HTTP listener, Dhan API, login, token renewal or Oracle runtime.
"""
import importlib.util
from pathlib import Path
import sys
import unittest

from pilot_v2.api_contract import make_snapshot
from pilot_v2.gateway_contract import ContractError
from pilot_v2.mobile_contract_mock import V2MobileFixture

path = Path(__file__).resolve().parents[1] / "android_app" / "src" / "quote_view.py"
spec = importlib.util.spec_from_file_location("ft2_quote_view", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

def quote(price, revision):
    return {"price": price, "freshness": "unverified", "live_verified": False,
            "revision": revision}

class GatewayToFletContractTests(unittest.TestCase):
    def setUp(self):
        self.gateway_fixture = V2MobileFixture()
        self.view = module.DeviceQuoteView()
        self.gateway_fixture.select({"watchlists": [["TCS"], ["INFY"], [], [], []]})

    def test_same_validated_message_reaches_both_local_consumers(self):
        payload = make_snapshot(1, {"TCS": quote(100, 1),
                                    "NIFTY": quote(25000, 1)})
        self.assertTrue(self.gateway_fixture.apply(payload))
        self.assertTrue(self.view.apply(payload, ("TCS", "INFY")))
        self.assertEqual(self.view.visible("TCS", ("TCS", "INFY"))["price"], 100)
        self.assertEqual(self.view.visible("NIFTY", ())["status"], "HIST")
        self.assertEqual(self.view.visible("INFY", ("TCS", "INFY"))["status"], "WAIT")
        self.assertNotIn("LIVE", self.view.display("TCS", ("TCS", "INFY")))

    def test_partial_and_empty_revision_retains_last_good_in_flet(self):
        first = make_snapshot(1, {"INFY": quote(1200, 1)})
        self.view.apply(first, ("TCS", "INFY"))
        self.view.apply(make_snapshot(2, {}), ("TCS", "INFY"))
        self.view.apply(make_snapshot(3, {"TCS": quote(110, 3)}), ("TCS", "INFY"))
        self.assertEqual(self.view.visible("INFY", ("TCS", "INFY"))["price"], 1200)
        self.assertFalse(self.view.apply(first, ("TCS", "INFY")))

    def test_unselected_quote_and_forged_live_flag_are_rejected(self):
        alien = make_snapshot(1, {"SBIN": quote(300, 1)})
        with self.assertRaises(ContractError):
            self.gateway_fixture.apply(alien)
        with self.assertRaises(module.FeedError):
            self.view.apply(alien, ("TCS", "INFY"))
        forged = make_snapshot(2, {"NIFTY": quote(25100, 2)})
        forged["quotes"]["NIFTY"]["live_verified"] = True
        with self.assertRaises(module.FeedError):
            self.view.apply(forged, ("TCS", "INFY"))
        self.assertEqual(self.view.revision, -1)

    def test_zero_selected_shares_still_allows_three_indices_only(self):
        view = module.DeviceQuoteView()
        payload = make_snapshot(1, {"SENSEX": quote(81000, 1)})
        self.assertTrue(view.apply(payload, ()))
        self.assertEqual(view.visible("SENSEX", ())["status"], "HIST")
        self.assertEqual(view.visible("TCS", ())["status"], "WAIT")

if __name__ == "__main__":
    unittest.main()
