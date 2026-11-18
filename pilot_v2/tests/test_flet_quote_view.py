"""Isolated Flet V2 quote view tests using only validated synthetic evidence."""
import importlib.util
import sys
from pathlib import Path
import unittest

file = Path(__file__).resolve().parents[1] / "android_app" / "src" / "quote_view.py"
spec = importlib.util.spec_from_file_location("v2_quote_view", file)
q = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = q
spec.loader.exec_module(q)

def snapshot(revision, quotes):
    return {"protocol": "botking-v2-readonly", "schema_version": 1, "source": "dhan",
            "freshness": "unverified", "live_orders_enabled": False,
            "revision": revision, "quotes": {symbol: {"price": price,
                "freshness": "unverified", "live_verified": False,
                "revision": revision} for symbol, price in quotes.items()}}

class DeviceQuoteViewTests(unittest.TestCase):
    def test_index_and_selected_quotes_partial_and_out_of_order(self):
        view = q.DeviceQuoteView()
        self.assertEqual(view.display("NIFTY", ()), "NIFTY — WAIT")
        self.assertTrue(view.apply(snapshot(1, {"NIFTY": 25000.5, "TCS": 100.0}), ("TCS",)))
        self.assertEqual(view.visible("TCS", ("TCS",))["status"], "HIST")
        self.assertIn("HIST (unverified)", view.display("NIFTY", ("TCS",)))
        self.assertTrue(view.apply(snapshot(2, {"NIFTY": 25010}), ("TCS",)))
        self.assertEqual(view.visible("TCS", ("TCS",))["price"], 100.0)
        self.assertFalse(view.apply(snapshot(1, {"TCS": 12}), ("TCS",)))
        self.assertEqual(view.visible("TCS", ("TCS",))["price"], 100.0)

    def test_atomic_reject_protected_foreign_live_and_bad_rows(self):
        view = q.DeviceQuoteView()
        self.assertTrue(view.apply(snapshot(2, {"TCS": 100}), ("TCS",)))
        bads = [
            snapshot(3, {"INFY": 10}),
            snapshot(3, {"TCS": -2}),
            dict(snapshot(3, {"TCS": 11}), source="yahoo"),
            dict(snapshot(3, {"TCS": 11}), live_orders_enabled=True),
            dict(snapshot(3, {"TCS": 11}), schema_version=True),
            dict(snapshot(3, {"TCS": 11}), token="secret"),
        ]
        injected = snapshot(3, {"TCS": 11, "NIFTY": 25200})
        injected["quotes"]["NIFTY"]["live_verified"] = True
        bads.append(injected)
        for bad in bads:
            with self.subTest(payload=repr(bad)[:110]), self.assertRaises(q.FeedError):
                view.apply(bad, ("TCS",))
            self.assertEqual(view.revision, 2)
            self.assertEqual(view.visible("TCS", ("TCS",))["price"], 100.0)

    def test_no_cross_watchlist_leak_and_removed_share_cleanup(self):
        view = q.DeviceQuoteView()
        view.apply(snapshot(1, {"NIFTY": 25000, "TCS": 100, "INFY": 200}), ("TCS","INFY"))
        self.assertEqual(view.visible("TCS", ())["status"], "WAIT")
        view.forget_removed(("INFY",))
        self.assertEqual(view.visible("TCS", ("TCS",))["status"], "WAIT")
        self.assertEqual(view.visible("INFY", ("INFY",))["status"], "HIST")
        self.assertEqual(view.visible("NIFTY", ())["status"], "HIST")
        with self.assertRaises(q.FeedError):
            view.apply(snapshot(2, {}), ("TCS","TCS"))

    def test_empty_authenticated_revision_keeps_existing_rows(self):
        view = q.DeviceQuoteView()
        view.apply(snapshot(1, {"BANKNIFTY": 60000}), ())
        self.assertTrue(view.apply(snapshot(2, {}), ()))
        self.assertEqual(view.visible("BANKNIFTY", ())["price"], 60000.0)
        self.assertEqual(view.visible("SENSEX", ())["status"], "WAIT")

if __name__ == "__main__":
    unittest.main()
