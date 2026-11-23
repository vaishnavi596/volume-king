"""Isolated Box Six HTTP staging API contracts; no real sockets/prod provider."""
import pathlib
import sys
import tempfile
import unittest
from fastapi.testclient import TestClient
from cryptography.fernet import Fernet

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from v3_brain_staging_api import create_staging_app

CREDS = {"phone1": "staging-local-device-proof-1000",
         "phone2": "staging-local-device-proof-2000",
         "phone3": "staging-local-device-proof-3000",
         "phone4": "staging-local-device-proof-4000"}


class BrainApiContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.key = Fernet.generate_key()
        self.app = create_staging_app(
            database=pathlib.Path(self.temp.name) / "staging.sqlite",
            device_credentials=CREDS, backup_key=self.key)
        self.client = TestClient(self.app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.temp.cleanup()

    def headers(self, device="phone1", proof=None):
        return {"X-Brain-Device": device,
                "X-Brain-Proof": CREDS[device] if proof is None else proof}

    def payload(self):
        return {"event_id": "phone1:prediction:0001", "kind": "prediction_event",
                "created_at": 1795440000,
                "payload": {"symbol": "NIFTY", "timeframe": "1m",
                            "prediction": "WAIT", "verified_live": False}}

    def test_denies_unauthenticated_and_bad_proof(self):
        self.assertEqual(self.client.get("/brain/v1/health").status_code, 401)
        self.assertEqual(self.client.get("/brain/v1/health",
                         headers=self.headers(proof="bad")).status_code, 403)
        self.assertEqual(self.client.get("/brain/v1/health",
                         headers=self.headers()).json()["status"], "STANDBY")

    def test_cross_phone_replay_idempotence_and_conflict(self):
        data = self.payload()
        first = self.client.post("/brain/v1/events", headers=self.headers(), json=data)
        self.assertEqual(first.status_code, 201)
        again = self.client.post("/brain/v1/events", headers=self.headers(), json=data)
        self.assertTrue(again.json()["idempotent_replay"])
        second = self.client.get("/brain/v1/sync", headers=self.headers("phone2"))
        self.assertEqual(second.status_code, 200)
        self.assertEqual(len(second.json()["events"]), 1)
        self.assertFalse(second.json()["live_eligible"])
        altered = {**data, "payload": {"symbol": "RELIANCE"}}
        self.assertEqual(self.client.post("/brain/v1/events", headers=self.headers(),
                         json=altered).status_code, 409)
        later = self.client.get("/brain/v1/sync?since=1",
                                headers=self.headers("phone3")).json()
        self.assertEqual(later["events"], [])
        self.assertEqual(later["next_cursor"], 1)

    def test_backup_encrypted_offline_restore_never_mutates_live(self):
        self.client.post("/brain/v1/events", headers=self.headers(), json=self.payload())
        blob = self.client.get("/brain/v1/backup", headers=self.headers("phone4"))
        self.assertEqual(blob.status_code, 200)
        self.assertNotIn(b"NIFTY", blob.content)
        self.assertIn(b"SQLite format 3", Fernet(self.key).decrypt(blob.content))
        info = self.client.get("/brain/v1/restore", headers=self.headers()).json()
        self.assertFalse(info["automatic_restore"])
        self.assertFalse(info["overwrite_allowed"])
        self.assertEqual(self.client.post("/brain/v1/restore",
                         headers=self.headers()).status_code, 405)

    def test_secret_rejected_and_no_broker_order_routes(self):
        bad = {**self.payload(), "event_id": "phone1:secret:0002",
               "payload": {"api_key": "nope"}}
        self.assertEqual(self.client.post("/brain/v1/events",
                         headers=self.headers(), json=bad).status_code, 422)
        self.assertEqual(self.client.post("/brain/v1/orders",
                         headers=self.headers()).status_code, 404)
        self.assertEqual(self.client.get("/brain/v1/sync?limit=501",
                         headers=self.headers()).status_code, 422)


if __name__ == "__main__":
    unittest.main()
