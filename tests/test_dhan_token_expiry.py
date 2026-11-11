"""Expiry parsing must fail closed on malformed or expired profile data."""
import unittest
from datetime import datetime, timezone
from backend.dhan_token_expiry import parse_profile_expiry


class DhanTokenExpiryTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 10, 6, 0, tzinfo=timezone.utc)

    def test_ist_profile_expiry_converts_to_utc(self):
        self.assertEqual(parse_profile_expiry("11/11/2026 12:01", self.now),
                         "2026-11-11T06:31:00+00:00")

    def test_expired_profile_rejected(self):
        with self.assertRaises(ValueError):
            parse_profile_expiry("09/11/2026 12:01", self.now)

    def test_missing_and_ambiguous_expiry_rejected(self):
        for value in (None, "", "2026-11-11", "11/11/2026", "invalid"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_profile_expiry(value, self.now)

    def test_naive_now_rejected(self):
        with self.assertRaises(ValueError):
            parse_profile_expiry("11/11/2026 12:01", datetime(2026, 11, 10))


if __name__ == "__main__":
    unittest.main()
