"""Offline tests for expiry-gated Dhan renewal scheduling."""
import unittest
from datetime import datetime, timezone
from backend.dhan_renewal_scheduler import scheduled_decision


class RenewalSchedulerTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 10, 8, 0, tzinfo=timezone.utc)

    def test_early_renewal_waits(self):
        result = scheduled_decision("dhan_web", "2026-11-11T12:01:00+05:30", now=self.now)
        self.assertEqual(result["state"], "valid")

    def test_due_web_token(self):
        result = scheduled_decision("dhan_web", "2026-11-10T15:00:00+05:30", now=self.now)
        self.assertEqual(result["state"], "renewal_due")

    def test_unknown_provenance_blocks(self):
        result = scheduled_decision("unknown", "2026-11-10T15:00:00+05:30", now=self.now)
        self.assertFalse(result["renew_token_allowed"])

    def test_expired_token_blocks(self):
        result = scheduled_decision("dhan_web", "2026-11-10T12:00:00+05:30", now=self.now)
        self.assertEqual(result["state"], "expired")

    def test_bad_expiry_fails_closed(self):
        with self.assertRaises(ValueError):
            scheduled_decision("dhan_web", "not-a-date", now=self.now)


if __name__ == "__main__":
    unittest.main()
