"""Offline bridge tests; synthetic tokens and temporary directories only."""
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from dhan_session_bridge import persist_verified_consent, load_verified_token, persist_consent_if_enabled


class DhanSessionBridgeTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 9, 12, tzinfo=timezone.utc)
        self.good = {
            "dhanClientId": "TEST_CLIENT",
            "accessToken": "FAKE_TOKEN_NEW",
            "expiryTime": "2026-11-10T12:00:00Z",
        }

    def test_persist_then_reload_after_new_call(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "dhan-token"
            expiry = persist_verified_consent(self.good, "TEST_CLIENT", path, self.now)
            self.assertEqual(expiry, datetime(2026, 11, 10, 12, tzinfo=timezone.utc))
            self.assertEqual(load_verified_token(path), "FAKE_TOKEN_NEW")

    def test_opt_in_disabled_never_creates_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "dhan-token"
            result = persist_consent_if_enabled(self.good, "TEST_CLIENT", {
                "DHAN_TOKEN_FILE": str(path),
                "DHAN_PERSIST_CONSENT_TOKEN": "0",
            }, self.now)
            self.assertIsNone(result)
            self.assertFalse(path.exists())

    def test_opt_in_enabled_writes_validated_token(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "dhan-token"
            result = persist_consent_if_enabled(self.good, "TEST_CLIENT", {
                "DHAN_TOKEN_FILE": str(path),
                "DHAN_PERSIST_CONSENT_TOKEN": "1",
            }, self.now)
            self.assertEqual(result, datetime(2026, 11, 10, 12, tzinfo=timezone.utc))
            self.assertEqual(load_verified_token(path), "FAKE_TOKEN_NEW")

    def test_opt_in_rejects_bad_account_without_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "dhan-token"
            config = {"DHAN_TOKEN_FILE": str(path), "DHAN_PERSIST_CONSENT_TOKEN": "1"}
            persist_consent_if_enabled(self.good, "TEST_CLIENT", config, self.now)
            with self.assertRaises(ValueError):
                persist_consent_if_enabled(dict(self.good, dhanClientId="WRONG"), "TEST_CLIENT", config, self.now)
            self.assertEqual(load_verified_token(path), "FAKE_TOKEN_NEW")

    def test_bad_consent_cannot_overwrite_existing_token(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "dhan-token"
            persist_verified_consent(self.good, "TEST_CLIENT", path, self.now)
            for altered in (
                dict(self.good, dhanClientId="WRONG"),
                dict(self.good, expiryTime="2026-11-08T12:00:00Z"),
                dict(self.good, expiryTime="2026-11-10T12:00:00"),
                dict(self.good, accessToken=""),
            ):
                with self.subTest(altered=sorted(altered.keys())):
                    with self.assertRaises(ValueError):
                        persist_verified_consent(altered, "TEST_CLIENT", path, self.now)
                    self.assertEqual(load_verified_token(path), "FAKE_TOKEN_NEW")


if __name__ == "__main__":
    unittest.main()
