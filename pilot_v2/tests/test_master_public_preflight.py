"""Offline synthetic gate tests; no physical-device evidence."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519

from pilot_v2.tools.master_public_preflight import inspect_public_handoff, main


class PublicHandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.path = self.directory / "master-public.der"
        key = ec.generate_private_key(ec.SECP256R1())
        self.data = key.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo)
        self.path.write_bytes(self.data)
        self.digest = hashlib.sha256(self.data).hexdigest()
        self.device = "real-android-master-0001"
        self.db = self.directory / "master.sqlite"
        self.db.write_bytes(b"immutable-existing-db")

    def check(self, **overrides):
        params = dict(device_id=self.device, public_path=self.path,
                      owner_fingerprint=self.digest)
        params.update(overrides)
        return inspect_public_handoff(**params)

    def test_exact_owner_approved_public_handoff_is_read_only(self):
        status = self.check()
        self.assertTrue(status["public_spki_verified"])
        self.assertFalse(status["enrolled"])
        self.assertFalse(status["android_runtime_verified"])
        self.assertFalse(status["oracle_activated"])
        self.assertFalse(status["orders_enabled"])
        self.assertEqual(self.db.read_bytes(), b"immutable-existing-db")
        self.assertEqual(self.path.read_bytes(), self.data)

    def test_mismatch_wrong_device_bad_hex_fail_closed(self):
        for update in ({"owner_fingerprint": "0" * 64},
                       {"owner_fingerprint": "z" * 64},
                       {"owner_fingerprint": "short"},
                       {"device_id": "bad device"}):
            with self.subTest(update=update), self.assertRaises(ValueError):
                self.check(**update)
        self.assertEqual(self.db.read_bytes(), b"immutable-existing-db")

    def test_reject_non_p256_malformed_and_symlink(self):
        bad = ed25519.Ed25519PrivateKey.generate().public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo)
        self.path.write_bytes(bad)
        with self.assertRaises(ValueError):
            self.check(owner_fingerprint=hashlib.sha256(bad).hexdigest())
        self.path.write_bytes(b"not-DER")
        with self.assertRaises(ValueError):
            self.check(owner_fingerprint=hashlib.sha256(b"not-DER").hexdigest())
        self.path.write_bytes(self.data)
        link = self.directory / "linked.der"
        link.symlink_to(self.path)
        with self.assertRaises(ValueError):
            self.check(public_path=link)
        self.assertEqual(self.db.read_bytes(), b"immutable-existing-db")

    def test_cli_never_claims_enrollment_or_live(self):
        import contextlib
        import io
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            result = main(["--device-id", self.device,
                           "--public-spki-der", str(self.path),
                           "--owner-fingerprint", self.digest])
        output = stream.getvalue()
        self.assertIn("V2_PUBLIC_HANDOFF_PREFLIGHT=PASS", output)
        self.assertIn("V2_MASTER_ENROLLED=NO", output)
        self.assertIn("V2_LIVE_ACTIVATED=NO", output)
        self.assertFalse(result["enrolled"])


if __name__ == "__main__":
    unittest.main()
