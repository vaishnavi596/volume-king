"""Offline restart-session tests with fake Dhan profile responses."""
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from dhan_restart_validation import verify_persisted_session
from dhan_token_storage import atomic_store_token


class RestartValidationTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 9, 12, tzinfo=timezone.utc)
        self.profile = {"dhanClientId": "TEST_ACCOUNT", "tokenValidity": "2026-11-10T09:43:00+05:30"}

    def test_valid_profile_allows_session(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "token"
            atomic_store_token(path, "FAKE_TOKEN")
            token, expiry = verify_persisted_session(path, "TEST_ACCOUNT", lambda t: self.profile, self.now)
            self.assertEqual(token, "FAKE_TOKEN")
            self.assertEqual(expiry, datetime(2026, 11, 10, 4, 13, tzinfo=timezone.utc))

    def test_wrong_account_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "token"
            atomic_store_token(path, "FAKE_TOKEN")
            with self.assertRaises(ValueError):
                verify_persisted_session(path, "OTHER_ACCOUNT", lambda t: self.profile, self.now)

    def test_naive_provider_timestamp_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "token"
            atomic_store_token(path, "FAKE_TOKEN")
            profile = dict(self.profile, tokenValidity="10/11/2026 09:43")
            with self.assertRaises(ValueError):
                verify_persisted_session(path, "TEST_ACCOUNT", lambda t: profile, self.now)

    def test_provider_date_requires_explicit_timezone(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "token"
            atomic_store_token(path, "FAKE_TOKEN")
            profile = dict(self.profile, tokenValidity="10/11/2026 09:43")
            token, expiry = verify_persisted_session(
                path, "TEST_ACCOUNT", lambda t: profile, self.now,
                provider_timezone="Asia/Kolkata")
            self.assertEqual(token, "FAKE_TOKEN")
            self.assertEqual(expiry, datetime(2026, 11, 10, 4, 13, tzinfo=timezone.utc))

    def test_invalid_provider_timezone_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "token"
            atomic_store_token(path, "FAKE_TOKEN")
            profile = dict(self.profile, tokenValidity="10/11/2026 09:43")
            with self.assertRaises(ValueError):
                verify_persisted_session(
                    path, "TEST_ACCOUNT", lambda t: profile, self.now,
                    provider_timezone="Not/A_Real_Zone")

    def test_expired_token_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "token"
            atomic_store_token(path, "FAKE_TOKEN")
            profile = dict(self.profile, tokenValidity="2026-11-08T12:00:00Z")
            with self.assertRaises(ValueError):
                verify_persisted_session(path, "TEST_ACCOUNT", lambda t: profile, self.now)

    def test_network_failure_never_falls_back_to_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "token"
            atomic_store_token(path, "FAKE_TOKEN")
            def network_failure(token):
                raise ConnectionError("simulated")
            with self.assertRaises(ConnectionError):
                verify_persisted_session(path, "TEST_ACCOUNT", network_failure, self.now)

    def test_missing_token_fails_before_profile_lookup(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(FileNotFoundError):
                verify_persisted_session(Path(folder) / "missing", "TEST_ACCOUNT",
                                         lambda t: self.profile, self.now)


if __name__ == "__main__":
    unittest.main()
