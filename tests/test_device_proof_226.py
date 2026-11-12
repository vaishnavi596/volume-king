"""Offline device proof checks; skip crypto-specific test if dependency absent."""
import base64
import importlib.util
import unittest
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "backend" / "device_proof_226.py"
spec = importlib.util.spec_from_file_location("botking_device_proof_226", path)
proof = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proof)


class DeviceProofTests(unittest.TestCase):
    @unittest.skipUnless(proof.ec is not None, "cryptography unavailable")
    def test_android_keystore_p256_signature(self):
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives import hashes, serialization
        private = ec.generate_private_key(ec.SECP256R1())
        public = private.public_key().public_bytes(
            serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
        challenge = proof.new_challenge()
        signature = private.sign(
            b"BOTKING226:DEVICE-AUTH:v1:" + base64.urlsafe_b64decode(challenge),
            ec.ECDSA(hashes.SHA256()))
        encode = lambda data: base64.urlsafe_b64encode(data).decode("ascii")
        self.assertTrue(proof.verify_android_p256_signature(
            encode(public), challenge, encode(signature)))
        self.assertFalse(proof.verify_android_p256_signature(
            encode(public), proof.new_challenge(), encode(signature)))

    def test_challenge_unique(self):
        self.assertNotEqual(proof.new_challenge(), proof.new_challenge())

    def test_single_use_and_expiry(self):
        now = [100.0]
        store = proof.ChallengeStore(clock=lambda: now[0])
        device = "android_owner_device_226"
        challenge = store.issue(device)
        self.assertTrue(store.consume(device, challenge))
        self.assertFalse(store.consume(device, challenge))
        challenge = store.issue(device)
        now[0] += 121
        self.assertFalse(store.consume(device, challenge))

    def test_device_scoping(self):
        store = proof.ChallengeStore()
        challenge = store.issue("android_owner_device_226")
        self.assertFalse(store.consume("android_other_device_226", challenge))
        self.assertTrue(store.consume("android_owner_device_226", challenge))

    def test_bad_proof_rejected(self):
        with self.assertRaises(proof.DeviceProofError):
            proof.verify_device_signature("not-base64!", "x", "x")

    @unittest.skipUnless(proof.Ed25519PublicKey is not None, "cryptography unavailable")
    def test_signature_and_replay_domain(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization
        private = Ed25519PrivateKey.generate()
        public = private.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw)
        challenge = proof.new_challenge()
        raw_challenge = base64.urlsafe_b64decode(challenge)
        signature = private.sign(b"BOTKING226:DEVICE-AUTH:v1:" + raw_challenge)
        encode = lambda raw: base64.urlsafe_b64encode(raw).decode("ascii")
        self.assertTrue(proof.verify_device_signature(
            encode(public), challenge, encode(signature)))
        self.assertFalse(proof.verify_device_signature(
            encode(public), proof.new_challenge(), encode(signature)))


if __name__ == "__main__":
    unittest.main()
