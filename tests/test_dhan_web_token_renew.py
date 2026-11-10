"""Offline tests for opt-in Dhan Web token rotation."""
import json
import fcntl
import os
from pathlib import Path
import tempfile
import unittest
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
            return Response({"dhanClientId": "12345"})
        result = renew_web_token("12345", self.path, opener)
        self.assertTrue(result["profile_verified"])
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

    def test_invalid_renewal_response_does_not_replace_token(self):
        with self.assertRaises(ValueError):
            renew_web_token("12345", self.path, lambda req, timeout: Response({"status": "error"}))
        self.assertEqual(self.path.read_text(), self.old)

    def test_existing_lock_blocks_second_renewal(self):
        lock_path = self.path.with_name(self.path.name + ".lock")
        with open(lock_path, "w") as held:
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
