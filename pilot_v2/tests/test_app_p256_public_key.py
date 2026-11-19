"""Offline public-only contract for future Android Keystore key enrollment."""
import sys
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from app_p256_public_key import (
    canonical_p256_public_spki, export_validated_p256_public_spki)


def public_der(key):
    return key.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo)


class AndroidPublicKeyBoundaryTests(unittest.TestCase):
    def test_generated_p256_public_key_roundtrips_without_private_export(self):
        private = ec.generate_private_key(ec.SECP256R1())
        good = public_der(private)
        self.assertEqual(len(good), 91)
        self.assertTrue(canonical_p256_public_spki(good))
        calls = []
        def public_only():
            calls.append("public")
            return good
        self.assertEqual(export_validated_p256_public_spki(public_only), good)
        self.assertEqual(calls, ["public"])

    def test_wrong_curve_private_der_and_malformed_points_rejected(self):
        k = ec.generate_private_key(ec.SECP256R1())
        valid = public_der(k)
        private_der = k.private_bytes(
            serialization.Encoding.DER,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption())
        wrong_curve = public_der(ec.generate_private_key(ec.SECP384R1()))
        bad = (None, True, "public", b"", valid[:-1], valid + b"\x00",
               wrong_curve, private_der, valid[:27] + bytes(64),
               valid[:32] + bytes([valid[32] ^ 1]) + valid[33:],
               bytearray(valid))
        for sample in bad:
            with self.subTest(value=type(sample).__name__, size=len(sample) if hasattr(sample, "__len__") else 0):
                self.assertFalse(canonical_p256_public_spki(sample))
                with self.assertRaises(ValueError):
                    export_validated_p256_public_spki(lambda sample=sample: sample)

    def test_export_errors_are_sanitized(self):
        def leak_alias():
            raise RuntimeError("private-keystore-alias-secret")
        with self.assertRaises(ValueError) as err:
            export_validated_p256_public_spki(leak_alias)
        self.assertNotIn("private-keystore-alias-secret", str(err.exception))
        self.assertIsNone(err.exception.__cause__)
        with self.assertRaises(ValueError):
            export_validated_p256_public_spki("not callable")


if __name__ == "__main__":
    unittest.main()
