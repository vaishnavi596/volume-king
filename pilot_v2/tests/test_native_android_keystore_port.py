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
        self.assertEqual(_safe_byte_string([255, 128, 0, 127]), b"\xff\x80\x00\x7f")
        for bad_values in ([256], [-129], [1024], [True], ["3"], [None]):
            with self.subTest(value=bad_values), self.assertRaises(FeedError):
                _safe_byte_string(bad_values)

    def test_native_direct_sign_method_never_signs_arbitrary_bytes(self):
        # Direct access to the adapter must not bypass the binding's
        # exact domain separation and owner-approved device identity.
        adapter = AndroidNativeP256Provider(DEVICE, autoclass=fake_autoclass)
        adapter.ensure_public_spki()
        prefix = LOGIN_CONTEXT + DEVICE.encode("ascii") + bytes([0])
        bad = (b"", b"ORDER", prefix, prefix + bytes(31),
               prefix + bytes(33), b"OTHER" + prefix + bytes(32),
               "not-bytes", bytearray(prefix + bytes(32)))
        for message in bad:
            with self.subTest(message=repr(message)[:32]), self.assertRaises(FeedError):
                adapter.sign_login_message(message)
        signed = prefix + bytes(range(32))
        signature = adapter.sign_login_message(signed)
        FakeKeyStore.keys[adapter.alias].public_key().verify(
            signature, signed, ec.ECDSA(hashes.SHA256()))

    def test_key_replacement_denied_by_existing_binding(self):
        adapter = AndroidNativeP256Provider(DEVICE, autoclass=fake_autoclass)
        adapter.ensure_public_spki()
        binding = adapter.binding()
        FakeKeyStore.keys[adapter.alias] = ec.generate_private_key(ec.SECP256R1())
        msg = LOGIN_CONTEXT + DEVICE.encode("ascii") + b"\x00" + bytes(32)
        with self.assertRaises(FeedError):
            binding.sign_login_challenge(msg)

    def test_flet_025_native_dependency_pinned_but_not_runtime_proof(self):
        import tomllib
        config = tomllib.loads(
            (SRC.parent / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(config["project"]["dependencies"],
                         ["flet==0.25.2", "pyjnius==1.6.1"])
        # Neither a Python wheel pin nor mock Java tests authorize an APK,
        # Android Keystore attestation or automatic signed-in status.
        source = (SRC / "app_native_keystore.py").read_text(encoding="utf-8")
        self.assertIn("from jnius import autoclass", source)
        self.assertIn("Android Keystore native runtime not installed", source)
        self.assertNotIn("import jnius\n", (SRC / "main.py").read_text())

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
