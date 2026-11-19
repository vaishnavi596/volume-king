"""V2 sealed private preference storage: offline-only, no server or secrets."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pilot_v2.durable_device_sessions import DurableDeviceSessions
from pilot_v2.device_sessions import VerifiedDevice
from pilot_v2.private_backup_vault import (
    PrivateBackupDenied, ServerBackupVault, inspect_envelope,
    seal_local_preferences, unseal_local_preferences, create_private_backup_router,
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

    def test_real_durable_master_session_revoke_rotate_and_expiry(self):
        with tempfile.TemporaryDirectory() as d:
            now = [1000.0]
            sessions = DurableDeviceSessions(
                Path(d) / "sessions.sqlite", clock=lambda: now[0], ttl=60)
            master_id = "master_authorized_0001"
            delegate_id = "delegate_authorized_0001"
            sessions.bootstrap(master_id, authorize_bootstrap=lambda _: True)
            master = sessions.issue_verified(VerifiedDevice(master_id))
            sessions.master_grant(master, delegate_id, ["quotes"])
            delegate = sessions.issue_verified(VerifiedDevice(delegate_id))
            vault = ServerBackupVault.from_durable_sessions(
                Path(d) / "vault.sqlite", sessions)
            sealed = seal_local_preferences(BACKUP, PASSWORD)
            self.assertEqual(vault.replace(master, sealed, expected_revision=0), 1)
            with self.assertRaises(PrivateBackupDenied):
                vault.read(delegate)
            with self.assertRaises(PrivateBackupDenied):
                vault.replace(delegate, sealed, expected_revision=1)
            fresh = sessions.issue_verified(VerifiedDevice(master_id))
            with self.assertRaises(PrivateBackupDenied):
                vault.read(master)
            self.assertEqual(vault.read(fresh), (1, sealed))
            sessions.logout(fresh)
            with self.assertRaises(PrivateBackupDenied):
                vault.read(fresh)
            renewed = sessions.issue_verified(VerifiedDevice(master_id))
            now[0] += 60
            with self.assertRaises(PrivateBackupDenied):
                vault.read(renewed)

    def test_invalid_base64_fails_cleanly(self):
        item = json.loads(seal_local_preferences(BACKUP, PASSWORD))
        item["salt"] = "!!!not valid!!!"
        with self.assertRaises(PrivateBackupDenied):
            inspect_envelope(json.dumps(item))

    def test_opt_in_http_routes_authorize_master_and_reject_plaintext(self):
        with tempfile.TemporaryDirectory() as d:
            sessions = DurableDeviceSessions(
                Path(d) / "sessions.sqlite", clock=lambda: 1000., ttl=60)
            master_id, delegate_id = ("master_private_0001", "delegate_private_0001")
            sessions.bootstrap(master_id, authorize_bootstrap=lambda _: True)
            master = sessions.issue_verified(VerifiedDevice(master_id))
            sessions.master_grant(master, delegate_id, ["quotes"])
            delegate = sessions.issue_verified(VerifiedDevice(delegate_id))
            vault = ServerBackupVault.from_durable_sessions(
                Path(d) / "private.sqlite", sessions)
            app = FastAPI()
            app.include_router(create_private_backup_router(vault))
            client = TestClient(app, base_url="https://testserver")
            insecure = TestClient(app, base_url="http://testserver")
            url = "/v2-pilot/private-backup"
            auth = {"Authorization": "Bearer " + master}
            bad = {"Authorization": "Bearer " + delegate}
            self.assertEqual(insecure.get(url).status_code, 403)
            self.assertEqual(client.get(url).status_code, 401)
            self.assertEqual(client.get(url, headers=bad).status_code, 403)
            self.assertEqual(client.get(url, headers=auth).json(),
                             {"revision": 0, "encrypted_envelope": None})
            encrypted = seal_local_preferences(BACKUP, PASSWORD)
            self.assertEqual(insecure.post(url, headers=auth, json={
                "encrypted_envelope": encrypted, "expected_revision": 0
            }).status_code, 403)
            post = client.post(url, headers=auth, json={
                "encrypted_envelope": encrypted, "expected_revision": 0})
            self.assertEqual(post.status_code, 200)
            self.assertEqual(post.json()["revision"], 1)
            self.assertEqual(post.headers["cache-control"], "no-store")
            self.assertEqual(client.get(url, headers=auth).json(),
                             {"revision": 1, "encrypted_envelope": encrypted})
            self.assertEqual(client.post(url, headers=bad, json={
                "encrypted_envelope": encrypted, "expected_revision": 1}).status_code, 403)
            self.assertEqual(client.post(url, headers=auth, json={
                "encrypted_envelope": encrypted, "expected_revision": 0}).status_code, 409)
            self.assertEqual(client.post(url, headers=auth, json={
                "plaintext": BACKUP, "password": PASSWORD}).status_code, 400)
            sessions.logout(master)
            self.assertEqual(client.get(url, headers=auth).status_code, 403)

    def test_session_revoked_between_checks_returns_403_without_write(self):
        with tempfile.TemporaryDirectory() as d:
            calls = [0]
            def master_owner(token):
                calls[0] += 1
                if calls[0] > 1:
                    raise PermissionError("session no longer valid")
                return "master-authorized-0001"
            vault = ServerBackupVault(Path(d) / "vault.sqlite",
                                      master_owner=master_owner)
            app = FastAPI()
            app.include_router(create_private_backup_router(vault))
            client = TestClient(app, base_url="https://testserver")
            encrypted = seal_local_preferences(BACKUP, PASSWORD)
            response = client.post("/v2-pilot/private-backup",
                headers={"Authorization": "Bearer " + "a" * 48},
                json={"encrypted_envelope": encrypted, "expected_revision": 0})
            self.assertEqual(response.status_code, 403)
            self.assertEqual(calls[0], 2)
            with vault._db() as db:
                count = db.execute("SELECT COUNT(*) FROM private_backups").fetchone()[0]
            self.assertEqual(count, 0)

    def test_db_replacement_symlink_and_exposed_permissions_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            db_path = Path(d) / "vault.sqlite"
            owner = lambda _: "master-authorized-0001"
            vault = ServerBackupVault(db_path, master_owner=owner)
            sealed = seal_local_preferences(BACKUP, PASSWORD)
            self.assertEqual(vault.replace("master", sealed, expected_revision=0), 1)
            db_path.chmod(0o644)
            with self.assertRaises(VaultStorageDenied):
                vault.read("master")
            db_path.chmod(0o600)
            self.assertEqual(vault.read("master")[0], 1)
            original = Path(d) / "original.sqlite"
            db_path.rename(original)
            db_path.symlink_to(original)
            with self.assertRaises(VaultStorageDenied):
                vault.read("master")
            db_path.unlink()
            original.rename(db_path)
            self.assertEqual(vault.read("master")[0], 1)
            other = Path(d) / "other.sqlite"
            db_path.rename(other)
            other_bytes = other.read_bytes()
            db_path.write_bytes(other_bytes)
            db_path.chmod(0o600)
            with self.assertRaises(VaultStorageDenied):
                vault.replace("master", sealed, expected_revision=1)

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
