"""Source/JNI contract tests: mock Java only; NOT Android runtime acceptance."""
import ast
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from app_native_keystore import AndroidNativeP256Provider, _alias_for_device, _safe_byte_string
from app_p256_login import LOGIN_CONTEXT
from secure_https_reader import FeedError

DEVICE = "master_device_000001"


class FakeKeyStore:
    keys = {}
    def load(self, value):
        pass
    def containsAlias(self, alias):
        return alias in self.keys
    def getCertificate(self, alias):
        key = self.keys[alias]
        class Public:
            def getEncoded(self):
                return key.public_key().public_bytes(
                    serialization.Encoding.DER,
                    serialization.PublicFormat.SubjectPublicKeyInfo)
        class Cert:
            def getPublicKey(self):
                return Public()
        return Cert()
    def getKey(self, alias, unused):
        return self.keys.get(alias)


class FakeBuilder:
    def __init__(self, alias, purposes):
        self.alias = alias
    def setAlgorithmParameterSpec(self, spec):
        assert spec == "secp256r1"
    def setDigests(self, digest):
        assert digest == "SHA-256"
    def setUserAuthenticationRequired(self, value):
        assert value is False
    def build(self):
        return self.alias


class FakeGenerator:
    def initialize(self, alias):
        self.alias = alias
    def generateKeyPair(self):
        FakeKeyStore.keys[self.alias] = ec.generate_private_key(ec.SECP256R1())


class FakeSignature:
    def initSign(self, key):
        self.key = key
    def update(self, message):
        self.message = message
    def sign(self):
        return self.key.sign(self.message, ec.ECDSA(hashes.SHA256()))


def fake_autoclass(name):
    table = {
        "java.security.KeyStore": type("Store", (), {
            "getInstance": staticmethod(lambda name: FakeKeyStore())}),
        "java.security.KeyPairGenerator": type("Gen", (), {
            "getInstance": staticmethod(lambda algorithm, provider: FakeGenerator())}),
        "java.security.spec.ECGenParameterSpec": lambda name: name,
        "android.security.keystore.KeyProperties": type(
            "Properties", (), {"PURPOSE_SIGN": 4, "DIGEST_SHA256": "SHA-256"}),
        "android.security.keystore.KeyGenParameterSpec$Builder": FakeBuilder,
        "java.security.Signature": type("Signature", (), {
            "getInstance": staticmethod(lambda name: FakeSignature())}),
    }
    if name not in table:
        raise RuntimeError("unexpected Android class")
    return table[name]


class NativeKeystoreContractTests(unittest.TestCase):
    def setUp(self):
        FakeKeyStore.keys = {}

    def test_explicit_enrollment_only_then_signed_exact_challenge(self):
        adapter = AndroidNativeP256Provider(DEVICE, autoclass=fake_autoclass)
        self.assertEqual(FakeKeyStore.keys, {})
        with self.assertRaises(FeedError):
            adapter.binding()
        public = adapter.ensure_public_spki()
        self.assertGreater(len(public), 80)
        self.assertEqual(adapter.ensure_public_spki(), public)
        self.assertEqual(len(FakeKeyStore.keys), 1)
        binding = adapter.binding()
        self.assertEqual(binding.public_spki_for_owner_enrollment(), public)
        msg = LOGIN_CONTEXT + DEVICE.encode("ascii") + b"\x00" + bytes(range(32))
        signature = binding.sign_login_challenge(msg)
        FakeKeyStore.keys[adapter.alias].public_key().verify(
            signature, msg, ec.ECDSA(hashes.SHA256()))
        with self.assertRaises(FeedError):
            binding.sign_login_challenge(b"ORDER")
        self.assertEqual(len(FakeKeyStore.keys), 1)

    def test_missing_platform_and_invalid_alias_fail_closed(self):
        for bad in ("short", "bad device id", None):
            with self.subTest(value=bad), self.assertRaises(FeedError):
                _alias_for_device(bad)
        with self.assertRaises(FeedError):
            AndroidNativeP256Provider(DEVICE, autoclass=lambda name: None)
        adapter = AndroidNativeP256Provider(DEVICE, autoclass=fake_autoclass)
        with self.assertRaises(FeedError):
            adapter.sign_login_message(b"no-key")
        with self.assertRaises(FeedError):
            _safe_byte_string([0] * 1025)
        self.assertEqual(_safe_byte_string([-1, -128, 0, 127]), b"\xff\x80\x00\x7f")

    def test_key_replacement_denied_by_existing_binding(self):
        adapter = AndroidNativeP256Provider(DEVICE, autoclass=fake_autoclass)
        adapter.ensure_public_spki()
        binding = adapter.binding()
        FakeKeyStore.keys[adapter.alias] = ec.generate_private_key(ec.SECP256R1())
        msg = LOGIN_CONTEXT + DEVICE.encode("ascii") + b"\x00" + bytes(32)
        with self.assertRaises(FeedError):
            binding.sign_login_challenge(msg)

    def test_flet_settings_actions_are_real_but_no_automatic_login(self):
        source = (SRC / "main.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("on_click=prepare_native_device_enrollment", source)
        self.assertIn("on_click=sign_in_native_v2_device", source)
        self.assertIn("device_session_slot.sign_in_with_keystore(", source)
        self.assertIn("device_login_origin.value", source)
        self.assertNotIn("client_storage.set(device_login", source)
        self.assertIn("on_click=clear_local_device_session", source)
        native_source = (SRC / "app_native_keystore.py").read_text(encoding="utf-8")
        self.assertIn('getInstance("EC", "AndroidKeyStore")', native_source)
        self.assertNotIn("getPrivate().getEncoded(", native_source)


if __name__ == "__main__":
    unittest.main()
