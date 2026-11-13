"""Dhan option-chain adapter is read-only and validates inputs before network access."""
import unittest
from unittest.mock import patch
from backend.dhan_feed import DhanFeed, DhanFeedError


class OptionChainAdapterTests(unittest.TestCase):
    def setUp(self):
        self.feed = DhanFeed("client", "token")

    def test_valid_underlying_routes_only_to_optionchain(self):
        with patch.object(self.feed, "_post", return_value={"data": {}}) as post:
            self.feed.option_chain("IDX_I", 13, "2099-12-31")
            post.assert_called_once_with("/optionchain", {
                "UnderlyingScrip": 13, "UnderlyingSeg": "IDX_I", "Expiry": "2099-12-31"})

    def test_invalid_inputs_never_call_network(self):
        with patch.object(self.feed, "_post") as post:
            for segment, sid, expiry in [("NSE_FNO", 13, "2099-12-31"),
                                         ("IDX_I", True, "2099-12-31"),
                                         ("IDX_I", 0, "2099-12-31"),
                                         ("IDX_I", 13, "2020-01-01"),
                                         ("IDX_I", 13, "tomorrow")]:
                with self.subTest(segment=segment, sid=sid, expiry=expiry):
                    with self.assertRaises(DhanFeedError):
                        self.feed.option_chain(segment, sid, expiry)
            post.assert_not_called()

    def test_endpoint_allowlist_keeps_order_routes_blocked(self):
        with self.assertRaises(DhanFeedError):
            self.feed._post("/orders", {})


if __name__ == "__main__":
    unittest.main()
