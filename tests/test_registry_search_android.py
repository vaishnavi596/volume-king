"""Strict Oracle Registry lookup adapter; never infer equity from price."""
import unittest
from unittest.mock import patch
from market_feed import FeedError
from server_feed import ServerDhanReadOnly

class RegistrySearchTests(unittest.TestCase):
    def setUp(self):
        self.feed=ServerDhanReadOnly()
        self.feed._origin="https://example.org"
        self.feed._pairing_key="test-only"

    def test_exact_symbol_verified_without_quote(self):
        with patch.object(self.feed,"_call",return_value={
            "source":"dhan_registry","symbols":["RELIANCE"],
            "live_orders_enabled":False}) as call:
            self.assertTrue(self.feed.verified_equity_symbol("RELIANCE"))
        call.assert_called_once_with("/v2/instruments/search?q=RELIANCE&limit=1")

    def test_invalid_or_unauthorized_payload_never_adds_symbol(self):
        with patch.object(self.feed,"_call",return_value={
            "source":"dhan_registry","symbols":["OTHER"],"live_orders_enabled":False}):
            with self.assertRaises(FeedError):
                self.feed.verified_equity_symbol("RELIANCE")
        with patch.object(self.feed,"_call",side_effect=AssertionError("network")):
            for symbol in ("../ADMIN","reliance","", "X" * 33):
                with self.subTest(symbol=symbol),self.assertRaises(FeedError):
                    self.feed.verified_equity_symbol(symbol)
