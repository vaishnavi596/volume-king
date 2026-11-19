"""Offline security gates for the real V2 Oracle entrypoint; no network."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from pilot_v2.durable_device_sessions import DurableDeviceSessions
from pilot_v2.oracle_secure_entrypoint import create_app, from_private_config


class SecureEntrypointTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "v2-private"
        self.root.mkdir(mode=0o700)
        self.db = self.root / "master.db"
        self.der = self.root / "master.der"
        self.key = self.root / "pairing.key"
        self.device_id = "master-v2-android-001"
        signing = ec.generate_private_key(ec.SECP256R1())
        self.der.write_bytes(signing.public_key().public_bytes(
            serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo))
        self.key.write_text("P" * 40, encoding="ascii")
        self.der.chmod(0o600)
        self.key.chmod(0o600)

    def build(self):
        return from_private_config(device_id=self.device_id,
            master_der_path=str(self.der), pairing_path=str(self.key),
            db_path=str(self.db))

    def provision(self):
        sessions = DurableDeviceSessions(self.db)
        sessions.bootstrap(self.device_id,
            authorize_bootstrap=lambda identifier: identifier == self.device_id)
        self.db.chmod(0o600)

    def test_no_configuration_never_bootstraps(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                create_app()
        self.assertFalse(self.db.exists())

    def test_missing_master_cannot_launch_real_http(self):
        self.provision()
        # Deliberately unregistered device must be rejected by existing factory.
        with self.assertRaises(ValueError):
            from_private_config(device_id="other-master-android-1",
                master_der_path=str(self.der), pairing_path=str(self.key),
                db_path=str(self.db))
        client = TestClient(self.build())
        self.assertEqual(client.get("/v2-pilot/quotes").status_code, 401)
        self.assertEqual(client.get("/v2-pilot/orders").status_code, 404)

    def test_required_protected_material_and_no_fallback(self):
        with self.assertRaises(ValueError):
            self.build()
        self.provision()
        self.assertIsNotNone(self.build())
        self.key.chmod(0o644)
        with self.assertRaises(ValueError):
            self.build()
        self.key.chmod(0o600)
        self.root.chmod(0o755)
        with self.assertRaises(ValueError):
            self.build()
        self.root.chmod(0o700)
        alias = self.root / "alias"
        alias.symlink_to(self.key)
        with self.assertRaises(ValueError):
            from_private_config(device_id=self.device_id, master_der_path=str(self.der),
                pairing_path=str(alias), db_path=str(self.db))
        self.key.write_text("invalid\n", encoding="ascii")
        with self.assertRaises(ValueError):
            self.build()

    def test_non_p256_public_key_refused(self):
        self.provision()
        self.der.write_bytes(b"not-a-valid-public-key")
        with self.assertRaises(ValueError):
            self.build()


if __name__ == "__main__":
    unittest.main()
