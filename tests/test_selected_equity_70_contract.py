"""Fail-closed selected Dhan equity quote coverage up to 70 slots, offline."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from server_feed import FeedError, ServerDhanReadOnly


class SelectedEquity70ContractTests(unittest.TestCase):
    def setUp(self):
        self.feed = ServerDhanReadOnly()

    def test_exactly_70_selected_quotes_one_bounded_batch(self):
        symbols = [f"EQ{i:03d}" for i in range(70)]
        body = {
            "source": "dhan", "live_orders_enabled": False,
            "freshness": "unverified", "quote_timestamp": None,
            "quotes": {s: 100 + i for i, s in enumerate(symbols)},
            "unavailable": [],
        }
        with patch.object(self.feed, "_call", return_value=body) as call:
            rows = self.feed.selected_equity_quotes(symbols)
            self.assertEqual(set(rows), set(symbols))
            self.assertTrue(all(not v["live_verified"] for v in rows.values()))
            call.assert_called_once_with("/dhan/selected-ltp-batch",
                                         {"symbols": symbols})

    def test_input_rejects_71_duplicates_and_unhashable_without_request(self):
        symbols = [f"EQ{i:03d}" for i in range(70)]
        for bad in (symbols + ["EQ070"], ["HDFCBANK", "HDFCBANK"],
                    ["HDFCBANK", []], ["HDFCBANK", {"foo": 1}],
                    [], ["HDFC BANK"]):
            with self.subTest(bad=repr(bad)[:40]):
                with patch.object(self.feed, "_call") as call:
                    with self.assertRaises(FeedError):
                        self.feed.selected_equity_quotes(bad)
                    call.assert_not_called()

    def test_registry_response_must_be_valid_object_before_save(self):
        for invalid in (None, [], "error", 200):
            with self.subTest(invalid=type(invalid).__name__):
                with patch.object(self.feed, "_call", return_value=invalid):
                    with self.assertRaises(FeedError):
                        self.feed.verified_equity_symbol("HDFCBANK")
        with patch.object(self.feed, "_call", return_value={
            "source": "dhan_registry", "live_orders_enabled": False,
            "symbols": ["HDFCBANK"]}) as call:
            self.assertTrue(self.feed.verified_equity_symbol("HDFCBANK"))
            self.assertEqual(call.call_count, 1)

    def test_nonobject_response_and_bad_unavailable_fail_closed(self):
        for bad in (None, [], "server error",
                    {"source": "dhan", "live_orders_enabled": False,
                     "freshness": "unverified", "quote_timestamp": None,
                     "quotes": {}, "unavailable": [[]]},
                    {"source": "dhan", "live_orders_enabled": False,
                     "freshness": "unverified", "quote_timestamp": None,
                     "quotes": {}, "unavailable": [{"bad": 1}]}):
            with self.subTest(result=repr(bad)[:50]):
                with patch.object(self.feed, "_call", return_value=bad):
                    with self.assertRaises(FeedError):
                        self.feed.selected_equity_quotes(["HDFCBANK"])


if __name__ == "__main__":
    unittest.main()
