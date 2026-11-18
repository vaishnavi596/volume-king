"""FT-2 separate revision lanes: synthetic app-only receiver, no HTTP/broker."""
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(ROOT))
from feed_inbox import DeviceFeedInbox, FeedError  # noqa: E402


def payload(revision, prices):
    return {"protocol": "botking-v2-readonly", "schema_version": 1,
            "source": "dhan", "freshness": "unverified",
            "live_orders_enabled": False, "revision": revision,
            "quotes": {sym: {"price": price, "freshness": "unverified",
                             "live_verified": False, "revision": revision}
                       for sym, price in prices.items()}}


class SeparateFeedLaneTests(unittest.TestCase):
    def test_indices_high_revision_does_not_block_equities_low_revision(self):
        view = DeviceFeedInbox()
        self.assertTrue(view.apply_feed("indices", payload(200, {"NIFTY": 25000}), ("TCS",)))
        self.assertTrue(view.apply_feed("quotes", payload(1, {"TCS": 100}), ("TCS",)))
        self.assertEqual(view.revision_for("indices"), 200)
        self.assertEqual(view.revision_for("quotes"), 1)
        self.assertEqual(view.visible("TCS", ("TCS",))["price"], 100)
        self.assertEqual(view.visible("NIFTY", ())["price"], 25000)
        self.assertIn("HIST (unverified)", view.display("NIFTY", ()))

    def test_equities_high_revision_does_not_block_indices_low_revision(self):
        view = DeviceFeedInbox()
        self.assertTrue(view.apply_feed("quotes", payload(77, {"TCS": 100}), ("TCS",)))
        self.assertTrue(view.apply_feed("indices", payload(2, {"SENSEX": 82000}), ("TCS",)))
        self.assertEqual(view.revision_for("indices"), 2)
        self.assertEqual(view.visible("TCS", ("TCS",))["price"], 100)
        self.assertFalse(view.apply_feed("quotes", payload(77, {"TCS": 900}), ("TCS",)))
        self.assertTrue(view.apply_feed("quotes", payload(78, {}), ("TCS",)))
        self.assertEqual(view.visible("TCS", ("TCS",))["price"], 100)

    def test_cross_feed_injection_and_invalid_source_reject_atomically(self):
        view = DeviceFeedInbox()
        view.apply_feed("indices", payload(1, {"BANKNIFTY": 60000}), ("TCS",))
        for feed, bad in (
                ("quotes", payload(2, {"NIFTY": 25100})),
                ("indices", payload(2, {"TCS": 110})),
                ("quotes", dict(payload(2, {"TCS": 110}), source="yahoo")),
                ("indices", dict(payload(2, {"NIFTY": 25100}), live_orders_enabled=True)),
                ("candles", payload(2, {"TCS": 110}))):
            with self.subTest(feed=feed), self.assertRaises(FeedError):
                view.apply_feed(feed, bad, ("TCS",))
        self.assertEqual(view.revision_for("quotes"), -1)
        self.assertEqual(view.revision_for("indices"), 1)
        self.assertEqual(view.visible("BANKNIFTY", ())["price"], 60000)

    def test_selection_changes_remain_app_owned_with_three_indexes(self):
        view = DeviceFeedInbox()
        view.apply_feed("quotes", payload(1, {"TCS": 100, "INFY": 1000}), ("TCS", "INFY"))
        view.apply_feed("indices", payload(2, {"NIFTY": 25000}), ("TCS", "INFY"))
        view.forget_removed(("INFY",))
        self.assertEqual(view.visible("TCS", ("TCS",))["status"], "WAIT")
        self.assertEqual(view.visible("INFY", ("INFY",))["price"], 1000)
        self.assertEqual(view.visible("NIFTY", ())["price"], 25000)
        with self.assertRaises(FeedError):
            view.apply_feed("quotes", payload(3, {}), ("INFY", "INFY"))
        with self.assertRaises(FeedError):
            view.revision_for("options")


if __name__ == "__main__":
    unittest.main()
