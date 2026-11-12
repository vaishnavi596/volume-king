"""Fail-closed native Android bridge contract tests; no biometric claim."""
import asyncio
import base64
import sys
import unittest
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from android_device_auth_226 import AndroidDeviceAuthBridge, AndroidAuthUnavailable


class NativeStub:
    async def generate_p256_key(self, device_id):
        self.key = ec.generate_private_key(ec.SECP256R1())
        der = self.key.public_key().public_bytes(serialization.Encoding.DER,
                                                serialization.PublicFormat.SubjectPublicKeyInfo)
        return base64.urlsafe_b64encode(der).decode("ascii")

    async def sign_challenge_with_biometric(self, device_id, challenge):
        if not hasattr(self, "key"):
            self.key = ec.generate_private_key(ec.SECP256R1())
        signature = self.key.sign(b"BOTKING226:DEVICE-AUTH:v1:" +
                                  base64.urlsafe_b64decode(challenge), ec.ECDSA(hashes.SHA256()))
        return base64.urlsafe_b64encode(signature).decode("ascii")


class AndroidBridgeTests(unittest.TestCase):
    def test_missing_native_bridge_fails_closed(self):
        with self.assertRaises(AndroidAuthUnavailable):
            AndroidDeviceAuthBridge(None)
        with self.assertRaises(AndroidAuthUnavailable):
            AndroidDeviceAuthBridge(object())

    def test_native_bridge_contract(self):
        bridge = AndroidDeviceAuthBridge(NativeStub())
        registered = asyncio.run(bridge.register_key("android_device_226"))
        self.assertTrue(registered.public_key.startswith("p256:"))
        challenge = base64.urlsafe_b64encode(b"y" * 32).decode("ascii")
        signature = asyncio.run(bridge.sign_login_challenge("android_device_226", challenge))
        self.assertTrue(signature)

    def test_fake_public_key_rejected(self):
        class FakeKey(NativeStub):
            async def generate_p256_key(self, device_id):
                return base64.urlsafe_b64encode(b"x" * 91).decode("ascii")
        with self.assertRaises(AndroidAuthUnavailable):
            asyncio.run(AndroidDeviceAuthBridge(FakeKey()).register_key("android_device_226"))

    def test_fake_signature_rejected(self):
        class FakeSignature(NativeStub):
            async def sign_challenge_with_biometric(self, device_id, challenge):
                return base64.urlsafe_b64encode(b"x" * 70).decode("ascii")
        challenge = base64.urlsafe_b64encode(b"y" * 32).decode("ascii")
        with self.assertRaises(AndroidAuthUnavailable):
            asyncio.run(AndroidDeviceAuthBridge(FakeSignature()).sign_login_challenge(
                "android_device_226", challenge))

    def test_invalid_challenge_never_reaches_native(self):
        bridge = AndroidDeviceAuthBridge(NativeStub())
        with self.assertRaises(ValueError):
            asyncio.run(bridge.sign_login_challenge("android_device_226", "bad"))


if __name__ == "__main__":
    unittest.main()
