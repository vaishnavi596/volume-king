"""App-only feed/cache regression: keep last-good symbols, isolate lanes."""
import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from feed_inbox import DeviceFeedInbox
from quote_view import FeedError


def snapshot(revision, quotes):
    return {
        "protocol": "botking-v2-readonly", "schema_version": 1,
        "source": "dhan", "freshness": "unverified",
        "live_orders_enabled": False, "revision": revision,
        "quotes": {
            symbol: {"price": price, "freshness": "unverified",
                     "live_verified": False, "revision": row_revision}
            for symbol, (price, row_revision) in quotes.items()
        },
    }


class FeedLastGoodRegression(unittest.TestCase):
    def setUp(self):
        self.feed = DeviceFeedInbox()
        self.selected = ("TCS", "INFY")

    def test_stale_symbol_row_cannot_replace_last_good_on_new_envelope(self):
        self.assertTrue(self.feed.apply_feed("quotes", snapshot(
            10, {"TCS": (120, 10), "INFY": (200, 8)}), self.selected))
        self.assertTrue(self.feed.apply_feed("quotes", snapshot(
            11, {"TCS": (99, 9), "INFY": (205, 11)}), self.selected))
        self.assertEqual(self.feed.visible("TCS", self.selected)["price"], 120)
        self.assertEqual(self.feed.visible("INFY", self.selected)["price"], 205)
        self.assertEqual(self.feed.revision_for("quotes"), 11)

    def test_empty_and_malformed_failures_retain_last_good_and_index_lane(self):
        self.feed.apply_feed("quotes", snapshot(4, {"TCS": (120, 4)}),
                             self.selected)
        self.feed.apply_feed("indices", snapshot(5, {"NIFTY": (23000, 5)}),
                             self.selected)
        self.feed.apply_feed("quotes", snapshot(6, {}), self.selected)
        self.assertEqual(self.feed.visible("TCS", self.selected)["price"], 120)
        for bad_roster in (("TCS", ["INFY"]), ("TCS", "TCS"),
                           ("NIFTY",), tuple("EQ" + str(i) for i in range(71))):
            with self.subTest(roster=str(bad_roster)[:25]):
                with self.assertRaises(FeedError):
                    self.feed.apply_feed("quotes", snapshot(7, {}),
                                         bad_roster)
        with self.assertRaises(FeedError):
            self.feed.apply_feed("quotes", snapshot(7, {"NIFTY": (1, 7)}),
                                 self.selected)
        self.assertEqual(self.feed.visible("TCS", self.selected)["price"], 120)
        self.assertEqual(self.feed.visible("NIFTY", self.selected)["price"], 23000)
        self.assertEqual(self.feed.revision_for("indices"), 5)

    def test_data_only_delta_ignores_stale_or_noop_envelopes(self):
        self.feed.apply_feed("quotes", snapshot(
            10, {"TCS": (120, 10)}), self.selected)
        self.assertEqual(self.feed.changed_for("quotes"), ("TCS",))
        self.feed.apply_feed("indices", snapshot(
            3, {"NIFTY": (22000, 3)}), self.selected)
        self.assertEqual(self.feed.changed_for("indices"), ("NIFTY",))
        self.feed.apply_feed("quotes", snapshot(
            11, {"TCS": (110, 9)}), self.selected)
        self.assertEqual(self.feed.changed_for("quotes"), ())
        self.assertEqual(self.feed.changed_for("indices"), ("NIFTY",))
        self.feed.apply_feed("quotes", snapshot(12, {}), self.selected)
        self.assertEqual(self.feed.changed_for("quotes"), ())
        self.assertEqual(self.feed.visible("TCS", self.selected)["price"], 120)
        self.assertFalse(self.feed.apply_feed(
            "quotes", snapshot(12, {"TCS": (130, 12)}), self.selected))
        self.assertEqual(self.feed.changed_for("quotes"), ())
        self.feed.apply_feed("quotes", snapshot(
            13, {"TCS": (130, 13)}), self.selected)
        self.assertEqual(self.feed.changed_for("quotes"), ("TCS",))
        with self.assertRaises(FeedError):
            self.feed.changed_for("bad")

    def test_removed_equity_does_not_erase_independent_index(self):
        self.feed.apply_feed("quotes", snapshot(2, {"TCS": (120, 2)}),
                             self.selected)
        self.feed.apply_feed("indices", snapshot(3, {"NIFTY": (22000, 3)}),
                             self.selected)
        self.feed.forget_removed(("INFY",))
        self.assertEqual(self.feed.visible("TCS", ("INFY",))["status"], "WAIT")
        self.assertEqual(self.feed.visible("NIFTY", ("INFY",))["price"], 22000)


if __name__ == "__main__":
    unittest.main()
