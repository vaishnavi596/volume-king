"""Regression checks for Dhan server key encoding without exposing secrets."""
import unittest
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from market_feed import FeedError
from server_feed import checked_pairing_key


class DhanPairingHeaderTests(unittest.TestCase):
    def test_ascii_key_remains_unchanged(self):
        self.assertEqual(checked_pairing_key("AaZz09-_="), "AaZz09-_=")

    def test_unicode_and_whitespace_are_rejected_before_network(self):
        for value in ("abc\u2013def", "abc\u00a0def", "abc def", "\tabc", "abc\n"):
            with self.subTest(value=repr(value)):
                with self.assertRaises(FeedError) as exc:
                    checked_pairing_key(value)
                self.assertNotIn(value,str(exc.exception))

    def test_missing_key_rejected(self):
        with self.assertRaises(FeedError):
            checked_pairing_key("")


if __name__ == "__main__":
    unittest.main()
