"""Offline registry tests; no Oracle production routes enabled."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.device_registry_226 import DeviceRegistry, DeviceRegistryError


class Registry226Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.now = [1000]
        self.path = Path(self.temp.name) / "registry.db"
        self.registry = DeviceRegistry(self.path, clock=lambda: self.now[0])
        self.device = "android_owner_226_0001"
        self.public_key = "public-device-key-placeholder-for-tests"

    def enroll(self):
        self.registry.enroll_approved_device(
            self.device, self.public_key, owner_approved=True
        )

    def test_challenge_single_use_across_restart(self):
        self.enroll()
        challenge = self.registry.issue_challenge(self.device)
        restarted = DeviceRegistry(self.path, clock=lambda: self.now[0])
        self.assertTrue(restarted.consume_challenge(self.device, challenge))
        self.assertFalse(self.registry.consume_challenge(self.device, challenge))
        self.assertNotIn(challenge.encode(), self.path.read_bytes())

    def test_challenge_expires(self):
        self.enroll()
        challenge = self.registry.issue_challenge(self.device)
        self.now[0] += 121
        self.assertFalse(self.registry.consume_challenge(self.device, challenge))

    def test_persistent_login_lockout(self):
        self.enroll()
        for _ in range(4):
            self.assertTrue(self.registry.record_login_failure(self.device))
        self.assertFalse(self.registry.record_login_failure(self.device))
        restarted = DeviceRegistry(self.path, clock=lambda: self.now[0])
        self.assertFalse(restarted.login_allowed(self.device))
        self.assertFalse(restarted.clear_login_failures(self.device))
        self.now[0] += 901
        self.assertTrue(restarted.login_allowed(self.device))
        self.assertTrue(restarted.clear_login_failures(self.device))

    def test_private_database_permissions(self):
        self.assertEqual(self.path.stat().st_mode & 0o077, 0)

    def test_existing_public_database_rejected(self):
        os.chmod(self.path, 0o644)
        with self.assertRaises(DeviceRegistryError):
            DeviceRegistry(self.path)

    def test_invalid_device_id_rejected(self):
        self.assertFalse(self.registry.validate_session("../wrong", "x" * 40))
        with self.assertRaises(DeviceRegistryError):
            self.registry.issue_session("../wrong", device_proof_verified=True)

    def test_owner_approval_required(self):
        with self.assertRaises(DeviceRegistryError):
            self.registry.enroll_approved_device(self.device, self.public_key)

    def test_proof_required(self):
        self.enroll()
        with self.assertRaises(DeviceRegistryError):
            self.registry.issue_session(self.device)

    def test_session_expiry_and_persistence(self):
        self.enroll()
        token = self.registry.issue_session(self.device, device_proof_verified=True)
        other = DeviceRegistry(self.path, clock=lambda: self.now[0])
        self.assertTrue(other.validate_session(self.device, token))
        self.now[0] += 901
        self.assertFalse(other.validate_session(self.device, token))

    def test_multiple_sessions(self):
        self.enroll()
        first = self.registry.issue_session(self.device, device_proof_verified=True)
        second = self.registry.issue_session(self.device, device_proof_verified=True)
        self.assertTrue(self.registry.validate_session(self.device, first))
        self.assertTrue(self.registry.validate_session(self.device, second))

    def test_revoked_device_blocks_sessions(self):
        self.enroll()
        token = self.registry.issue_session(self.device, device_proof_verified=True)
        self.registry.revoke_device(self.device)
        self.assertFalse(self.registry.validate_session(self.device, token))
        with self.assertRaises(DeviceRegistryError):
            self.registry.issue_session(self.device, device_proof_verified=True)

    def test_revoked_session(self):
        self.enroll()
        token = self.registry.issue_session(self.device, device_proof_verified=True)
        self.registry.revoke_session(token)
        self.assertFalse(self.registry.validate_session(self.device, token))

    def test_no_raw_token_stored(self):
        self.enroll()
        token = self.registry.issue_session(self.device, device_proof_verified=True)
        self.assertNotIn(token.encode(), self.path.read_bytes())


if __name__ == "__main__":
    unittest.main()
