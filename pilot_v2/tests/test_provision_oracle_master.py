"""Local-only owner-approved Oracle V2 Master enrollment tests."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from pilot_v2.tools.provision_oracle_master import enroll_master, main


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

    def test_production_cli_rejects_non_v2_directory_before_any_enrollment(self):
        # An operator cannot accidentally enroll into V1 or a similarly
        # named path: no file or stdout exposing details is produced.
        args = ["provision_oracle_master.py", "--private-directory", str(self.root),
                "--device-id", self.device_id, "--public-spki-der",
                str(self.public), "--approved-public-sha256", self.digest]
        with patch.object(sys, "argv", args), self.assertRaises(SystemExit) as error:
            main()
        self.assertEqual(error.exception.code, 2)
        self.assertFalse((self.root / "master.sqlite").exists())
        self.assertEqual(list(self.root.glob(".master-enroll-*")), [])

    def test_production_cli_rejects_v2_private_directory_lookalike(self):
        args = ["provision_oracle_master.py", "--private-directory",
                "/home/opc/botking-v2-private-copy", "--device-id",
                self.device_id, "--public-spki-der", str(self.public),
                "--approved-public-sha256", self.digest]
        with patch.object(sys, "argv", args), self.assertRaises(SystemExit) as error:
            main()
        self.assertEqual(error.exception.code, 2)

    def test_explicit_approval_once_no_private_key(self):
        result=self.enroll()
        self.assertTrue(result["master_enrolled"])
        self.assertFalse(result["private_key_exported"])
        self.assertFalse(result["orders_enabled"])
        self.assertEqual((self.root/"master.sqlite").stat().st_mode & 0o777,0o600)
        with self.assertRaises(ValueError):
            self.enroll()

    def test_failure_after_bootstrap_leaves_no_partial_master_and_retry_succeeds(self):
        # A failure between Master record creation and key enrollment must
        # not leave an incomplete irreversible master.sqlite.
        with patch("pilot_v2.tools.provision_oracle_master.DurableDeviceKeys",
                   side_effect=RuntimeError("simulated database init failure")):
            with self.assertRaisesRegex(RuntimeError, "simulated database"):
                self.enroll()
        self.assertFalse((self.root / "master.sqlite").exists())
        self.assertEqual(list(self.root.glob(".master-enroll-*")), [])
        self.assertTrue(self.enroll()["master_enrolled"])

    def test_existing_master_database_must_never_be_replaced(self):
        db = self.root / "master.sqlite"
        db.write_bytes(b"preexisting-master-record")
        with self.assertRaises(ValueError):
            self.enroll()
        self.assertEqual(db.read_bytes(), b"preexisting-master-record")
        self.assertEqual(list(self.root.glob(".master-enroll-*")), [])

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
