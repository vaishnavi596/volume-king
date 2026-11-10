"""Tests for private expiry metadata storage; no broker network calls."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from backend.dhan_expiry_store import save_expiry_metadata, load_expiry_metadata


class DhanExpiryStoreTests(unittest.TestCase):
    def test_private_atomic_save(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "expiry.json"
            expiry = (datetime.now(timezone.utc) + timedelta(hours=20)).isoformat()
            result = save_expiry_metadata(target, expiry)
            self.assertTrue(result["saved"])
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            data = json.loads(target.read_text())
            self.assertEqual(data["source"], "dhan_web")
            self.assertEqual(data["expires_at"], expiry)
            self.assertNotIn("access_token", data)
            self.assertEqual(load_expiry_metadata(target)["expires_at"], expiry)

    def test_reject_bad_or_expired(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "expiry.json"
            for expiry in ("bad", "2026-01-01T00:00:00+00:00", "2030-01-01T00:00:00"):
                with self.subTest(expiry=expiry), self.assertRaises(ValueError):
                    save_expiry_metadata(target, expiry)
            self.assertFalse(target.exists())

    def test_reject_public_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "expiry.json"
            target.write_text("{}")
            target.chmod(0o644)
            expiry = (datetime.now(timezone.utc) + timedelta(hours=20)).isoformat()
            with self.assertRaises(ValueError):
                save_expiry_metadata(target, expiry)

    def test_reject_tampered_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "expiry.json"
            target.write_text('{"source":"oauth_consent","expires_at":"2030-01-01T00:00:00+00:00"}')
            target.chmod(0o600)
            with self.assertRaises(ValueError):
                load_expiry_metadata(target)

    def test_reject_public_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "expiry.json"
            target.write_text("{}")
            target.chmod(0o644)
            with self.assertRaises(ValueError):
                load_expiry_metadata(target)

    def test_reject_unknown_source(self):
        with tempfile.TemporaryDirectory() as directory:
            expiry = (datetime.now(timezone.utc) + timedelta(hours=20)).isoformat()
            with self.assertRaises(ValueError):
                save_expiry_metadata(Path(directory) / "expiry.json", expiry, "oauth_consent")


if __name__ == "__main__":
    unittest.main()
