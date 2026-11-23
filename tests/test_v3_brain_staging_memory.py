"""Offline Batch-1 safety tests for the separate M Brain staging ledger."""
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from v3_brain_staging_memory import StagingBrainLedger

AUTH = {"phone1": "device-local-master-proof-0001",
        "phone2": "device-local-master-proof-0002"}


class BrainMemoryStagingContracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = pathlib.Path(self.tmp.name) / "brain.sqlite"
        self.ledger = StagingBrainLedger(self.path, AUTH)

    def tearDown(self):
        self.ledger.close()
        self.tmp.cleanup()

    def event(self, **overrides):
        data = dict(device_id="phone1", credential=AUTH["phone1"],
                    event_id="phone1:test:100", kind="prediction_event",
                    created_at=1795440000,
                    payload={"symbol": "NIFTY", "timeframe": "1m",
                             "verdict": "WAIT", "verified_live": False})
        data.update(overrides)
        return data

    def test_append_only_idempotence_and_conflict(self):
        original = self.ledger.append(**self.event())
        self.assertEqual(original["sequence"], 1)
        self.assertFalse(original["idempotent_replay"])
        self.assertTrue(self.ledger.append(**self.event())["idempotent_replay"])
        with self.assertRaises(ValueError):
            self.ledger.append(**self.event(payload={"symbol": "RELIANCE"}))
        self.assertEqual(self.ledger.audit()["stored_events"], 1)

    def test_device_scoped_auth_and_four_phone_limit(self):
        with self.assertRaises(PermissionError):
            self.ledger.append(**self.event(credential="wrong"))
        with self.assertRaises(PermissionError):
            self.ledger.since(device_id="other", credential="unknown")
        with self.assertRaises(ValueError):
            StagingBrainLedger(":memory:", {str(i):"x"*20 for i in range(5)})
        self.assertEqual(self.ledger.since(device_id="phone2",
                                          credential=AUTH["phone2"]), [])

    def test_no_secret_payload_and_bounded_sync(self):
        with self.assertRaises(ValueError):
            self.ledger.append(**self.event(payload={"access_token": "secret"}))
        with self.assertRaises(ValueError):
            self.ledger.since(device_id="phone1", credential=AUTH["phone1"],
                              sequence=0, limit=1000)
        self.ledger.append(**self.event())
        rows = self.ledger.since(device_id="phone2", credential=AUTH["phone2"])
        self.assertEqual(len(rows), 1)
        self.assertNotIn("credential", rows[0])
        self.assertFalse(self.ledger.audit()["live_votes_enabled"])

    def test_encrypted_backup_and_restore_with_no_overwrite(self):
        try:
            from cryptography.fernet import Fernet
        except ImportError:
            with self.assertRaises(RuntimeError):
                self.ledger.encrypted_backup(device_id="phone1",
                    credential=AUTH["phone1"], encryption_key=b"invalid")
            return
        self.ledger.append(**self.event())
        key = Fernet.generate_key()
        encrypted = self.ledger.encrypted_backup(
            device_id="phone1", credential=AUTH["phone1"], encryption_key=key)
        self.assertNotIn(b"NIFTY", encrypted)
        restored_path = pathlib.Path(self.tmp.name) / "restore.sqlite"
        restored = StagingBrainLedger.restore_to_new(
            destination=restored_path, encrypted_blob=encrypted,
            encryption_key=key, device_credentials=AUTH)
        try:
            self.assertEqual(restored.audit()["stored_events"], 1)
            self.assertEqual(restored.since(
                device_id="phone2", credential=AUTH["phone2"])[0]["event_id"],
                             "phone1:test:100")
        finally:
            restored.close()
        with self.assertRaises(FileExistsError):
            StagingBrainLedger.restore_to_new(
                destination=restored_path, encrypted_blob=encrypted,
                encryption_key=key, device_credentials=AUTH)


if __name__ == "__main__":
    unittest.main()
