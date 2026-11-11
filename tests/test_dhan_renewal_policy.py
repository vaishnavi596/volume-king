"""Offline tests: renewal must never run on unknown or expired token sources."""
import unittest
from datetime import datetime, timedelta, timezone
from backend.dhan_renewal_policy import renewal_decision


class DhanRenewalPolicyTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 10, 6, 0, tzinfo=timezone.utc)

    def test_web_token_due(self):
        result = renewal_decision("dhan_web", self.now + timedelta(minutes=30), now=self.now)
        self.assertEqual(result["state"], "renewal_due")
        self.assertTrue(result["renew_token_allowed"])

    def test_web_token_not_due(self):
        result = renewal_decision("dhan_web", self.now + timedelta(hours=10), now=self.now)
        self.assertEqual(result["action"], "wait")

    def test_expired_web_token_cannot_renew(self):
        result = renewal_decision("dhan_web", self.now - timedelta(seconds=1), now=self.now)
        self.assertEqual(result["action"], "reauthenticate")
        self.assertFalse(result["renew_token_allowed"])

    def test_unknown_token_cannot_use_renew_endpoint(self):
        result = renewal_decision("unknown", self.now + timedelta(hours=1), now=self.now)
        self.assertFalse(result["renew_token_allowed"])

    def test_oauth_token_cannot_use_renew_endpoint(self):
        result = renewal_decision("oauth_consent", self.now + timedelta(hours=1), now=self.now)
        self.assertFalse(result["renew_token_allowed"])

    def test_naive_expiry_is_ist(self):
        expiry = datetime(2026, 11, 10, 12, 0)
        result = renewal_decision("dhan_web", expiry, now=self.now)
        self.assertEqual(result["state"], "renewal_due")

    def test_invalid_lead_time(self):
        with self.assertRaises(ValueError):
            renewal_decision("dhan_web", self.now, now=self.now, lead_minutes=True)


if __name__ == "__main__":
    unittest.main()
