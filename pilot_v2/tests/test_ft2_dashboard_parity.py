"""Synthetic V2 Dashboard parity / no-live-claims regression tests."""
from pathlib import Path
import sys
import unittest
SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from dashboard_parity import INDEXES, index_card_model, status_overview
from feed_inbox import DeviceFeedInbox
from evidence_inbox import DeviceEvidenceInbox


def snapshot(revision, data):
    return {"protocol": "botking-v2-readonly", "schema_version": 1,
            "source": "dhan", "freshness": "unverified",
            "live_orders_enabled": False, "revision": revision,
            "quotes": {symbol: {"price": price, "freshness": "unverified",
                                "live_verified": False, "revision": revision}
                       for symbol, price in data.items()}}


class DashboardParityTests(unittest.TestCase):
    def setUp(self):
        self.quote = DeviceFeedInbox()
        self.evidence = DeviceEvidenceInbox()

    def test_all_three_cards_1m_wait_sixth_blank_no_live(self):
        cards = [index_card_model(s, self.quote, self.evidence) for s in INDEXES]
        self.assertEqual(tuple(c["symbol"] for c in cards), INDEXES)
        for card in cards:
            self.assertEqual(card["status"], "WAIT")
            self.assertEqual(card["timeframe"], "1m")
            self.assertEqual(len(card["filters"]), 5)
            self.assertEqual(card["sixth"], ("", ""))
            self.assertNotIn("LIVE", card["price_label"])

    def test_index_one_lane_partial_and_last_good_preserved(self):
        self.quote.apply_feed("indices", snapshot(1, {"NIFTY": 25120}), ())
        first = index_card_model("NIFTY", self.quote, self.evidence)
        self.assertEqual(first["status"], "HIST")
        self.assertIn("25,120.00 HIST", first["price_label"])
        self.assertEqual(index_card_model("SENSEX", self.quote, self.evidence)["status"], "WAIT")
        self.quote.apply_feed("indices", snapshot(2, {}), ())
        self.assertEqual(index_card_model("NIFTY", self.quote, self.evidence)["price_label"],
                         first["price_label"])
        with self.assertRaises(ValueError):
            index_card_model("TCS", self.quote, self.evidence)

    def test_health_and_master_cannot_claim_connected(self):
        summary = status_overview(("TCS", "INFY"), self.quote, self.evidence)
        self.assertEqual(summary["equity_count"], 2)
        self.assertEqual(summary["index_quote_coverage"], 0)
        self.assertIn("OFFLINE", summary["feed"])
        self.assertIn("not connected", summary["master"])
        self.assertEqual(summary["orders"], "LIVE ORDERS OFF")

    def test_flet_uses_cards_and_master_status_not_controls(self):
        source = (SRC / "main.py").read_text(encoding="utf-8")
        self.assertIn('index_card_model(symbol, quote_view, evidence_inbox,', source)
        self.assertIn('status_overview(state.selected, quote_view, evidence_inbox)', source)
        self.assertIn('ft.Container(', source)
        self.assertIn('Enable / Disable / Revoke require verified device login', source)
        self.assertIn('ft.NavigationDestination(icon=ft.icons.DASHBOARD_OUTLINED', source)
        self.assertIn('ft.NavigationDestination(icon=ft.icons.LIST_ALT_OUTLINED', source)
        self.assertIn('ft.NavigationDestination(icon=ft.icons.SETTINGS_OUTLINED', source)


if __name__ == "__main__":
    unittest.main()
