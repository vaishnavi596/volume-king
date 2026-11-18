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

    def test_watchlist_quote_wrapper_accepts_seventy_unique_equities(self):
        symbols = [f"EQ{i:03d}" for i in range(70)]
        self.feed._selected_batch_missing = False
        with patch.object(self.feed, "selected_equity_quotes",
                          return_value={s: {"price": 100} for s in symbols}) as selected:
            rows = self.feed.equity_quotes_for_watchlist(symbols)
            self.assertEqual(len(rows), 70)
            selected.assert_called_once_with(symbols)

    def test_watchlist_quote_wrapper_rejects_overcap_and_duplicate_before_http(self):
        symbols = [f"EQ{i:03d}" for i in range(70)]
        for invalid in (symbols + ["EQ070"], ["TCS", "TCS"],
                        ["NIFTY"], ["BANKNIFTY"], ["SENSEX"]):
            with self.subTest(size=len(invalid)):
                with patch.object(self.feed, "selected_equity_quotes") as selected:
                    with self.assertRaises(FeedError):
                        self.feed.equity_quotes_for_watchlist(invalid)
                    selected.assert_not_called()

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

    def test_zero_five_fifty_one_seventy_rosters_use_zero_or_one_selected_call(self):
        # Behavioral request budget, never rely on synthetic quote freshness
        # to imply provider-liveness or an Android integration proof.
        for count in (0, 5, 51, 70):
            with self.subTest(count=count):
                symbols = [f"EQ{i:03d}" for i in range(count)]
                expected = {s: {"price": 100+i, "source": "Dhan",
                                "freshness": "unverified", "live_verified": False}
                            for i, s in enumerate(symbols)}
                with patch.object(self.feed, "selected_equity_quotes",
                                  return_value=expected) as selected, patch.object(
                                      self.feed, "equity_quotes_with_bootstrap") as fallback:
                    result = self.feed.equity_quotes_for_watchlist(symbols)
                    self.assertEqual(set(result), set(symbols))
                    self.assertEqual(selected.call_count, 0 if count == 0 else 1)
                    fallback.assert_not_called()
                    if count:
                        selected.assert_called_once_with(symbols)

    def test_wrapper_malformed_rosters_fail_as_feederror_before_network(self):
        invalid = ([["TCS"]], ["TCS", []], ["TCS", {"oops": 1}],
                   [None], [123], ["NIFTY"], ["lowercase"],
                   ["BAD SYMBOL"], ["TCS", "TCS"], ["TCS. NS"])
        for symbols in invalid:
            with self.subTest(symbols=repr(symbols)[:50]):
                with patch.object(self.feed, "selected_equity_quotes") as selected, patch.object(
                        self.feed, "equity_quotes_with_bootstrap") as fallback:
                    with self.assertRaises(FeedError):
                        self.feed.equity_quotes_for_watchlist(symbols)
                    selected.assert_not_called()
                    fallback.assert_not_called()

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
