"""V2 sealed private preference storage: offline-only, no server or secrets."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from pilot_v2.private_backup_vault import (
    PrivateBackupDenied, ServerBackupVault, inspect_envelope,
    seal_local_preferences, unseal_local_preferences,
)

BACKUP = json.dumps({"kind": "botking-v2-local-preferences",
    "schema_version": 1, "watchlists": {}, "scanner": {},
    "smart_data": {}, "analysis_slots": {}})
PASSWORD = "correct horse strong backup 2026"


class PrivateBackupVaultTests(unittest.TestCase):
    def test_encrypted_roundtrip_and_nondeterministic_seal(self):
        first = seal_local_preferences(BACKUP, PASSWORD)
        second = seal_local_preferences(BACKUP, PASSWORD)
        self.assertNotEqual(first, second)
        self.assertNotIn("watchlists", first)
        self.assertNotIn(PASSWORD, first)
        self.assertEqual(json.loads(unseal_local_preferences(first, PASSWORD)),
                         json.loads(BACKUP))
        with self.assertRaises(PrivateBackupDenied):
            unseal_local_preferences(first, "incorrect password 123")

    def test_tamper_malformed_and_secret_payload_rejected(self):
        sealed = seal_local_preferences(BACKUP, PASSWORD)
        doc = json.loads(sealed)
        doc["ciphertext"] = doc["ciphertext"][:-4] + "AAAA"
        with self.assertRaises(PrivateBackupDenied):
            unseal_local_preferences(json.dumps(doc), PASSWORD)
        for input_text in ("{}", json.dumps({**json.loads(BACKUP),
                                             "dhan_token": "unsafe"}),
                           "x" * 16385):
            with self.assertRaises(PrivateBackupDenied):
                seal_local_preferences(input_text, PASSWORD)
        with self.assertRaises(PrivateBackupDenied):
            seal_local_preferences(BACKUP, "short")

    def test_owner_isolation_optimistic_revision_and_restart(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "private.sqlite"
            authorized = {"master-A": "master-authorized-0001",
                          "master-B": "master-authorized-0002"}
            def verify(token):
                if token not in authorized:
                    raise PermissionError
                return authorized[token]
            vault = ServerBackupVault(db, master_owner=verify)
            sealed = seal_local_preferences(BACKUP, PASSWORD)
            self.assertEqual(vault.read("master-A"), (0, None))
            self.assertEqual(vault.replace("master-A", sealed,
                                           expected_revision=0), 1)
            self.assertEqual(vault.read("master-B"), (0, None))
            self.assertEqual(vault.read("master-A"), (1, sealed))
            with self.assertRaises(PrivateBackupDenied):
                vault.replace("master-A", sealed, expected_revision=0)
            with self.assertRaises(PrivateBackupDenied):
                vault.read("delegate")
            self.assertEqual(ServerBackupVault(db, master_owner=verify)
                             .read("master-A"), (1, sealed))
            self.assertEqual(os.stat(db).st_mode & 0o077, 0)
            raw = db.read_bytes()
            self.assertNotIn(PASSWORD.encode(), raw)
            self.assertNotIn(b"watchlists", raw)

    def test_auth_denial_precedes_envelope_storage(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "private.sqlite"
            def master(token):
                if token != "real-master":
                    raise PermissionError
                return "master-authorized-0001"
            vault = ServerBackupVault(db, master_owner=master)
            with self.assertRaises(PrivateBackupDenied):
                vault.replace("delegate", "invalid", expected_revision=0)
            with self.assertRaises(PrivateBackupDenied):
                vault.replace("real-master", "invalid", expected_revision=0)
            self.assertEqual(vault.read("real-master"), (0, None))


if __name__ == "__main__":
    unittest.main()
