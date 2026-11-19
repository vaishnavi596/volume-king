"""Strict local backup validation before/after injected crypto; no Android crypto claim."""
import json
import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))

from app_state import LocalWatchlists
from scanner_state import ScannerSelection
from smart_data import SmartDataSettings
from local_analysis_slots import LocalAnalysisSlots
from local_settings_backup import export_local_backup
from local_private_backup_bridge import (
    LocalPrivateBackupError, prepare_private_backup, preview_private_restore,
)
from pilot_v2.private_backup_vault import (
    seal_local_preferences, unseal_local_preferences,
)

class LocalPrivateBackupBridgeTests(unittest.TestCase):
    def setUp(self):
        self.watchlists = LocalWatchlists()
        self.watchlists.add(0, "TCS")
        self.scanner = ScannerSelection("TCS", "3m")
        self.smart = SmartDataSettings(False, 300)
        self.slots = LocalAnalysisSlots(["NIFTY", "TCS", "TCS"])
        self.plaintext = export_local_backup(
            self.watchlists, self.scanner, self.smart, self.slots)
        self.password = "a unique very long private password"

    def test_validated_roundtrip_requires_explicit_callbacks(self):
        called = []
        def seal(plain, password):
            called.append(("seal", plain, password))
            return seal_local_preferences(plain, password)
        encrypted = prepare_private_backup(self.plaintext, self.password, seal=seal)
        self.assertEqual(json.loads(encrypted)["version"], 1)
        self.assertEqual(called, [("seal", self.plaintext, self.password)])
        values = preview_private_restore(
            encrypted, self.password, unseal=unseal_local_preferences)
        self.assertEqual(values[0].groups[0], ["TCS"])
        self.assertEqual(values[1].symbol, "TCS")

    def test_malformed_backup_is_rejected_before_sealing(self):
        original = json.loads(self.plaintext)
        for extra in ({"dhan_token": "NOT_ALLOWED"},
                      {"server_url": "https://unsafe.example"}):
            obj = dict(original)
            obj.update(extra)
            called = []
            with self.assertRaises(LocalPrivateBackupError):
                prepare_private_backup(json.dumps(obj), self.password,
                                       seal=lambda *args: called.append(args))
            self.assertEqual(called, [])
        with self.assertRaises(LocalPrivateBackupError):
            prepare_private_backup("{}", self.password,
                                   seal=lambda *_: "encrypted")

    def test_decrypted_payload_must_pass_full_local_parser(self):
        wrong = json.dumps({"kind": "botking-v2-local-preferences",
                            "schema_version": 1, "watchlists": {},
                            "scanner": {}, "smart_data": {},
                            "analysis_slots": {}})
        with self.assertRaises(LocalPrivateBackupError):
            preview_private_restore(
                seal_local_preferences(self.plaintext, self.password),
                self.password, unseal=lambda *_: wrong)
        with self.assertRaises(LocalPrivateBackupError):
            preview_private_restore(
                seal_local_preferences(self.plaintext, self.password),
                self.password, unseal=lambda *_: (_ for _ in ()).throw(
                                        RuntimeError("SECRET INFORMATION")))

    def test_rejects_malformed_or_forged_envelopes_before_upload_or_decrypt(self):
        valid = seal_local_preferences(self.plaintext, self.password)
        doc = json.loads(valid)
        candidates = ["opaque ciphertext", "{}", json.dumps({**doc, "password": "leak"}),
                      json.dumps({**doc, "salt": "!!"}),
                      json.dumps({**doc, "version": True}),
                      json.dumps({**doc, "nonce": "AAAA"}),
                      json.dumps({**doc, "ciphertext": "AA=="})]
        for result in candidates:
            with self.subTest(result=result[:30]):
                with self.assertRaises(LocalPrivateBackupError):
                    prepare_private_backup(self.plaintext, self.password,
                                           seal=lambda *_: result)
                callback = []
                with self.assertRaises(LocalPrivateBackupError):
                    preview_private_restore(result, self.password,
                        unseal=lambda *args: callback.append(args))
                self.assertEqual(callback, [])
        self.assertEqual(
            preview_private_restore(valid, self.password,
                                    unseal=unseal_local_preferences)[0].groups[0],
            ["TCS"])

    def test_missing_crypto_and_bad_password_denied(self):
        with self.assertRaises(LocalPrivateBackupError):
            prepare_private_backup(self.plaintext, "short",
                                   seal=lambda *_: "encrypted")
        with self.assertRaises(LocalPrivateBackupError):
            prepare_private_backup(self.plaintext, self.password, seal=None)
        with self.assertRaises(LocalPrivateBackupError):
            preview_private_restore("encrypted", self.password, unseal=None)

    def test_no_server_or_network_dependency_in_app_bridge(self):
        source = (SRC / "local_private_backup_bridge.py").read_text()
        for forbidden in ("from pilot_v2", "import fastapi", "import httpx",
                          "import requests", "Dhan", "broker_token"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
