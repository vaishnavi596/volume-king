"""Offline tests for opt-in Dhan Web token rotation."""
import json
import fcntl
import os
from pathlib import Path
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from backend.dhan_expiry_store import load_expiry_metadata
from backend.dhan_web_token_renew import renew_web_token


class Response:
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, limit):
        return json.dumps(self.payload).encode()


class RenewalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "token"
        self.old = "old-token-" + "a" * 30
        self.new = "new-token-" + "b" * 30
        self.path.write_text(self.old)
        self.path.chmod(0o600)

    def test_validated_rotation(self):
        seen = []
        def opener(req, timeout):
            seen.append(req.full_url)
            if req.full_url.endswith("/RenewToken"):
                return Response({"accessToken": self.new})
            return Response({"dhanClientId": "12345", "tokenValidity": "11/11/2026 12:01"})
        result = renew_web_token("12345", self.path, opener)
        self.assertTrue(result["profile_verified"])
        self.assertEqual(result["expiry_time"], "11/11/2026 12:01")
        self.assertEqual(self.path.read_text().strip(), self.new)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(len(seen), 2)

    def test_wrong_account_does_not_replace_token(self):
        def opener(req, timeout):
            if req.full_url.endswith("/RenewToken"):
                return Response({"accessToken": self.new})
            return Response({"dhanClientId": "wrong"})
        with self.assertRaises(ValueError):
            renew_web_token("12345", self.path, opener)
        self.assertEqual(self.path.read_text(), self.old)
        recovery = self.path.with_name(self.path.name + ".recovery")
        self.assertEqual(recovery.read_text().strip(), self.new)
        self.assertEqual(recovery.stat().st_mode & 0o777, 0o600)

    def test_profile_network_failure_preserves_recovery_token(self):
        def opener(req, timeout):
            if req.full_url.endswith("/RenewToken"):
                return Response({"accessToken": self.new})
            raise OSError("profile unavailable")
        with self.assertRaises(OSError):
            renew_web_token("12345", self.path, opener)
        recovery = self.path.with_name(self.path.name + ".recovery")
        self.assertEqual(recovery.read_text().strip(), self.new)
        self.assertEqual(recovery.stat().st_mode & 0o777, 0o600)

    def test_expiry_persisted_and_recovery_removed(self):
        expiry = (datetime.now(ZoneInfo("Asia/Kolkata")) + timedelta(hours=20)).strftime("%d/%m/%Y %H:%M")
        metadata_path = self.path.with_name("expiry.json")
        def opener(req, timeout):
            if req.full_url.endswith("/RenewToken"):
                return Response({"accessToken": self.new})
            return Response({"dhanClientId": "12345", "tokenValidity": expiry})
        renew_web_token("12345", self.path, opener, expiry_path=metadata_path)
        self.assertEqual(self.path.read_text().strip(), self.new)
        self.assertFalse(self.path.with_name(self.path.name + ".recovery").exists())
        self.assertEqual(load_expiry_metadata(metadata_path)["source"], "dhan_web")

    def test_expiry_write_failure_preserves_recovery_and_blocks_repeat(self):
        """A rotated token must remain recoverable if metadata persistence fails."""
        from unittest.mock import patch
        expiry = (datetime.now(ZoneInfo("Asia/Kolkata")) + timedelta(hours=20)).strftime("%d/%m/%Y %H:%M")
        metadata_path = self.path.with_name("expiry.json")

        def opener(req, timeout):
            if req.full_url.endswith("/RenewToken"):
                return Response({"accessToken": self.new})
            return Response({"dhanClientId": "12345", "tokenValidity": expiry})

        with patch("backend.dhan_web_token_renew.save_expiry_metadata",
                   side_effect=OSError("simulated metadata write failure")):
            with self.assertRaises(OSError):
                renew_web_token("12345", self.path, opener, expiry_path=metadata_path)

        recovery = self.path.with_name(self.path.name + ".recovery")
        self.assertEqual(self.path.read_text().strip(), self.new)
        self.assertEqual(recovery.read_text().strip(), self.new)
        self.assertEqual(recovery.stat().st_mode & 0o777, 0o600)
        self.assertFalse(metadata_path.exists())
        with self.assertRaisesRegex(ValueError, "recovery"):
            renew_web_token("12345", self.path,
                            lambda req, timeout: self.fail("unexpected repeat rotation"),
                            expiry_path=metadata_path)

    def test_recovery_blocks_repeat_renewal_before_network(self):
        self.path.with_name(self.path.name + ".recovery").write_text(self.new)
        with self.assertRaisesRegex(ValueError, "recovery"):
            renew_web_token("12345", self.path, lambda req, timeout: self.fail("network called"))

    def test_invalid_renewal_response_does_not_replace_token(self):
        with self.assertRaises(ValueError):
            renew_web_token("12345", self.path, lambda req, timeout: Response({"status": "error"}))
        self.assertEqual(self.path.read_text(), self.old)

    def test_existing_lock_blocks_second_renewal(self):
        lock_path = self.path.with_name(self.path.name + ".lock")
        with open(lock_path, "w") as held:
            lock_path.chmod(0o600)
            fcntl.flock(held.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(ValueError, "already running"):
                renew_web_token("12345", self.path,
                                lambda req, timeout: self.fail("network called"))
        self.assertEqual(self.path.read_text(), self.old)

    def test_public_token_file_rejected_before_network(self):
        self.path.chmod(0o644)
        with self.assertRaises(ValueError):
            renew_web_token("12345", self.path, lambda req, timeout: self.fail("network called"))
        self.assertEqual(self.path.read_text(), self.old)


if __name__ == "__main__":
    unittest.main()
