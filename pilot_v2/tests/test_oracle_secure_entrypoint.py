"""Offline security gates for the real V2 Oracle entrypoint; no network."""
import os
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from pilot_v2.tools.provision_oracle_master import enroll_master
from pilot_v2.oracle_secure_entrypoint import create_app, from_private_config, _persist_selected_equities


class SecureEntrypointTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "v2-private"
        self.root.mkdir(mode=0o700)
        self.db = self.root / "master.sqlite"
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
        enroll_master(directory=self.root, device_id=self.device_id,
            public_path=self.der,
            approved_fingerprint=hashlib.sha256(self.der.read_bytes()).hexdigest())

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

    def test_explicit_private_expiry_evidence_opt_in_is_off_by_default(self):
        self.provision()
        absent = self.build()
        self.assertEqual(TestClient(absent).get("/v2-pilot/evidence").status_code, 401)
        enabled = from_private_config(
            device_id=self.device_id, master_der_path=str(self.der),
            pairing_path=str(self.key), db_path=str(self.db),
            expiry_evidence_symbol="NIFTY")
        self.assertEqual(TestClient(enabled).get("/v2-pilot/evidence").status_code, 401)
        for invalid in ("", "nifty", "NIFTY/../../orders"):
            with self.subTest(symbol=invalid), self.assertRaises(ValueError):
                from_private_config(
                    device_id=self.device_id, master_der_path=str(self.der),
                    pairing_path=str(self.key), db_path=str(self.db),
                    expiry_evidence_symbol=invalid)

    def test_private_expiry_and_3m_candle_sources_share_one_disabled_by_default_lane(self):
        self.provision()
        source_args = dict(device_id=self.device_id,
            master_der_path=str(self.der), pairing_path=str(self.key),
            db_path=str(self.db),
            expiry_evidence_symbol="NIFTY",
            candle_evidence_symbol="RELIANCE",
            candle_evidence_timeframe="3m")
        app = from_private_config(**source_args)
        # Constructing a secure app never contacts the Dhan provider.
        self.assertEqual(TestClient(app).get("/v2-pilot/evidence").status_code, 401)
        self.assertEqual(TestClient(app).get("/v2-pilot/orders").status_code, 404)
        for wrong in ("2m", "", "60m"):
            with self.subTest(frame=wrong), self.assertRaises(ValueError):
                from_private_config(**dict(source_args, candle_evidence_timeframe=wrong))
        with self.assertRaises(ValueError):
            from_private_config(**dict(source_args,
                candle_evidence_symbol="NIFTY/../../orders"))

    def test_private_selected_equities_applied_and_index_independent(self):
        self.provision()
        roster = self.root / "selected-equities.json"
        roster.write_text('["RELIANCE","TCS"]', encoding="utf-8")
        roster.chmod(0o600)
        app = from_private_config(device_id=self.device_id,
            master_der_path=str(self.der), pairing_path=str(self.key),
            db_path=str(self.db), selected_equities_path=str(roster))
        self.assertEqual(app.title, "BOT KING V2 Trusted Adapter")
        self.assertEqual(TestClient(app).get("/v2-pilot/health").status_code, 200)
        # Negative-auth cannot be bypassed by a real selected roster.
        self.assertEqual(TestClient(app).get("/v2-pilot/quotes").status_code, 401)

    def test_private_roster_symlink_duplicate_and_world_readable_denied(self):
        self.provision()
        roster = self.root / "selected-equities.json"
        roster.write_text('["RELIANCE","RELIANCE"]')
        roster.chmod(0o600)
        config = dict(device_id=self.device_id, master_der_path=str(self.der),
                      pairing_path=str(self.key), db_path=str(self.db),
                      selected_equities_path=str(roster))
        with self.assertRaises(ValueError):
            from_private_config(**config)
        roster.write_text('["RELIANCE"]')
        roster.chmod(0o644)
        with self.assertRaises(ValueError):
            from_private_config(**config)
        roster.chmod(0o600)
        link = self.root / "alias-roster.json"
        link.symlink_to(roster)
        config["selected_equities_path"] = str(link)
        with self.assertRaises(ValueError):
            from_private_config(**config)

    def test_roster_atomic_private_file_persistence_is_fail_closed(self):
        roster = self.root / "selected-equities.json"
        roster.write_text('["RELIANCE"]')
        roster.chmod(0o600)
        _persist_selected_equities(str(roster), ("TCS", "INFY"))
        self.assertEqual(roster.read_text(), '["TCS","INFY"]')
        self.assertEqual(roster.stat().st_mode & 0o777, 0o600)
        roster.chmod(0o644)
        with self.assertRaises(ValueError):
            _persist_selected_equities(str(roster), ("TCS",))
        self.assertEqual(roster.read_text(), '["TCS","INFY"]')
        alias = self.root / "alias.json"
        alias.symlink_to(roster)
        with self.assertRaises(ValueError):
            _persist_selected_equities(str(alias), ("TCS",))

    def test_non_p256_public_key_refused(self):
        self.provision()
        self.der.write_bytes(b"not-a-valid-public-key")
        with self.assertRaises(ValueError):
            self.build()


if __name__ == "__main__":
    unittest.main()
