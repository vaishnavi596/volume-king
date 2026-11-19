"""Local-only owner-approved Oracle V2 Master enrollment tests."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from pilot_v2.tools.provision_oracle_master import enroll_master


class MasterEnrollmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "v2"
        self.root.mkdir(mode=0o700)
        self.public = self.root / "master.der"
        self.device_id = "real-android-master-0001"
        private = ec.generate_private_key(ec.SECP256R1())
        data = private.public_key().public_bytes(
            serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
        self.public.write_bytes(data)
        self.digest = hashlib.sha256(data).hexdigest()

    def enroll(self, **kw):
        args=dict(directory=self.root, device_id=self.device_id,
                  public_path=self.public, approved_fingerprint=self.digest)
        args.update(kw)
        return enroll_master(**args)

    def test_explicit_approval_once_no_private_key(self):
        result=self.enroll()
        self.assertTrue(result["master_enrolled"])
        self.assertFalse(result["private_key_exported"])
        self.assertFalse(result["orders_enabled"])
        self.assertEqual((self.root/"master.sqlite").stat().st_mode & 0o777,0o600)
        with self.assertRaises(ValueError):
            self.enroll()

    def test_mismatched_owner_fingerprint_refused(self):
        with self.assertRaises(ValueError):
            self.enroll(approved_fingerprint="0"*64)
        self.assertFalse((self.root/"master.sqlite").exists())

    def test_world_readable_parent_refused(self):
        self.root.chmod(0o755)
        with self.assertRaises(ValueError):
            self.enroll()
        self.assertFalse((self.root/"master.sqlite").exists())

    def test_public_key_must_be_inside_private_directory(self):
        with self.assertRaises(ValueError):
            self.enroll(public_path=Path(self.tmp.name)/"other.der")

    def test_reject_ed25519_key(self):
        from cryptography.hazmat.primitives.asymmetric import ed25519
        bad=ed25519.Ed25519PrivateKey.generate().public_key().public_bytes(
            serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
        self.public.write_bytes(bad)
        with self.assertRaises(ValueError):
            self.enroll(approved_fingerprint=hashlib.sha256(bad).hexdigest())


if __name__=="__main__":
    unittest.main()
