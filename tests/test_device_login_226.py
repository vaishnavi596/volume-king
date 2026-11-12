"""Offline end-to-end device proof/session tests; no production routes."""
import base64
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.device_login_226 import DeviceLoginCoordinator, DeviceLoginError
from backend.device_registry_226 import DeviceRegistry
from backend.device_proof_226 import Ed25519PublicKey


@unittest.skipUnless(Ed25519PublicKey is not None, "cryptography unavailable")
class DeviceLoginTests(unittest.TestCase):
    def setUp(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.registry = DeviceRegistry(Path(self.temp.name) / "devices.db")
        self.private = Ed25519PrivateKey.generate()
        public = self.private.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw)
        self.public = base64.urlsafe_b64encode(public).decode("ascii")
        self.device = "android_owner_device_226"
        self.registry.enroll_approved_device(self.device, self.public, owner_approved=True)
        self.login = DeviceLoginCoordinator(self.registry)

    def signature(self, challenge):
        raw = base64.urlsafe_b64decode(challenge)
        return base64.urlsafe_b64encode(self.private.sign(
            b"BOTKING226:DEVICE-AUTH:v1:" + raw)).decode("ascii")

    def test_android_p256_login_issues_session(self):
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives import hashes, serialization
        private = ec.generate_private_key(ec.SECP256R1())
        public = private.public_key().public_bytes(
            serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
        p256_device = "android_p256_device_226"
        self.registry.enroll_approved_device(
            p256_device, "p256:" + base64.urlsafe_b64encode(public).decode("ascii"),
            owner_approved=True)
        challenge = self.login.begin(p256_device)
        signature = private.sign(
            b"BOTKING226:DEVICE-AUTH:v1:" + base64.urlsafe_b64decode(challenge),
            ec.ECDSA(hashes.SHA256()))
        token = self.login.complete(
            p256_device, challenge, base64.urlsafe_b64encode(signature).decode("ascii"))
        self.assertTrue(self.registry.validate_session(p256_device, token))
        with self.assertRaises(DeviceLoginError):
            self.login.complete(
                p256_device, challenge, base64.urlsafe_b64encode(signature).decode("ascii"))

    def test_signed_login_issues_session(self):
        challenge = self.login.begin(self.device)
        token = self.login.complete(self.device, challenge, self.signature(challenge))
        self.assertTrue(self.registry.validate_session(self.device, token))

    def test_replay_rejected(self):
        challenge = self.login.begin(self.device)
        signature = self.signature(challenge)
        self.login.complete(self.device, challenge, signature)
        with self.assertRaises(DeviceLoginError):
            self.login.complete(self.device, challenge, signature)

    def test_bad_signature_consumes_challenge(self):
        challenge = self.login.begin(self.device)
        with self.assertRaises(DeviceLoginError):
            self.login.complete(self.device, challenge, self.signature(self.login.begin(self.device)))
        with self.assertRaises(DeviceLoginError):
            self.login.complete(self.device, challenge, self.signature(challenge))

    def test_revocation_blocks_login(self):
        self.registry.revoke_device(self.device)
        with self.assertRaises(DeviceLoginError):
            self.login.begin(self.device)


if __name__ == "__main__":
    unittest.main()
