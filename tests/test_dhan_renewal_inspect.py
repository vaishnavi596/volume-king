"""Regression tests for read-only renewal inspection."""
import unittest
from datetime import datetime, timedelta, timezone
from backend.dhan_renewal_inspect import inspect


class DhanRenewalInspectTests(unittest.TestCase):
    def test_unknown_source_fails_closed(self):
        result = inspect("unknown", "2026-11-11T12:01:00+05:30",
                         now=datetime(2026, 11, 10, tzinfo=timezone.utc))
        self.assertFalse(result["renew_token_allowed"])

    def test_expired_token_requires_reauthentication(self):
        result = inspect("dhan_web", "2026-11-09T12:01:00+05:30",
                         now=datetime(2026, 11, 10, tzinfo=timezone.utc))
        self.assertEqual(result["state"], "expired")

    def test_invalid_timestamp_is_rejected(self):
        with self.assertRaises(ValueError):
            inspect("dhan_web", "invalid")

    def test_ist_expiry_without_offset(self):
        now = datetime(2026, 11, 11, 5, 31, tzinfo=timezone.utc)
        result = inspect("dhan_web", "2026-11-11T12:01:00", now=now)
        self.assertEqual(result["state"], "renewal_due")


if __name__ == "__main__":
    unittest.main()
