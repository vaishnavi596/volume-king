"""Offline tests for Dhan consent validation; no real account credentials."""
from datetime import datetime, timezone, timedelta
import unittest
from dhan_consent_validation import validate_consent_response


class ConsentValidationTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 9, 12, tzinfo=timezone.utc)
        self.payload = {
            "dhanClientId": "FAKE_CLIENT",
            "accessToken": "FAKE_TEST_TOKEN",
            "expiryTime": "2026-11-10T12:00:00+00:00",
        }

    def test_valid_consent(self):
        token, expiry = validate_consent_response(self.payload, "FAKE_CLIENT", self.now)
        self.assertEqual(token, "FAKE_TEST_TOKEN")
        self.assertGreater(expiry, self.now)

    def test_wrong_account_rejected(self):
        with self.assertRaises(ValueError):
            validate_consent_response(self.payload, "OTHER_CLIENT", self.now)

    def test_ambiguous_timezone_rejected(self):
        payload = dict(self.payload, expiryTime="2026-11-10T12:00:00")
        with self.assertRaises(ValueError):
            validate_consent_response(payload, "FAKE_CLIENT", self.now)

    def test_explicit_ist_naive_expiry_is_normalized(self):
        payload = dict(self.payload, expiryTime="2026-11-10T17:30:00")
        token, expiry = validate_consent_response(
            payload, "FAKE_CLIENT", self.now, naive_expiry_timezone="Asia/Kolkata")
        self.assertEqual(token, "FAKE_TEST_TOKEN")
        self.assertEqual(expiry, datetime(2026, 11, 10, 12, tzinfo=timezone.utc))

    def test_unsupported_timezone_rejected(self):
        payload = dict(self.payload, expiryTime="2026-11-10T17:30:00")
        with self.assertRaises(ValueError):
            validate_consent_response(
                payload, "FAKE_CLIENT", self.now, naive_expiry_timezone="UTC")

    def test_expired_naive_ist_rejected(self):
        payload = dict(self.payload, expiryTime="2026-11-09T17:29:00")
        with self.assertRaises(ValueError):
            validate_consent_response(
                payload, "FAKE_CLIENT", self.now, naive_expiry_timezone="Asia/Kolkata")

    def test_expired_consent_rejected(self):
        payload = dict(self.payload, expiryTime="2026-11-08T12:00:00Z")
        with self.assertRaises(ValueError):
            validate_consent_response(payload, "FAKE_CLIENT", self.now)

    def test_missing_or_multiline_token_rejected(self):
        for token in ("", None, "INVALID\nTOKEN", " trailing "):
            with self.subTest(token=repr(token)):
                with self.assertRaises(ValueError):
                    validate_consent_response(dict(self.payload, accessToken=token), "FAKE_CLIENT", self.now)


if __name__ == "__main__":
    unittest.main()
