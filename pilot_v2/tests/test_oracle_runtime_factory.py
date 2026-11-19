"""Oracle V2 composition acceptance without any real broker or SSH calls."""
import os
from pathlib import Path
import tempfile
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from pilot_v2.device_verifier import P256ChallengeVerifier, encode_b64
from pilot_v2.durable_device_sessions import DurableDeviceSessions
from pilot_v2.oracle_runtime_factory import create_oracle_v2_runtime
from pilot_v2.internal_dhan_read_port import DhanReadBatch


class OracleRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name) / "private"
        self.dir.mkdir(mode=0o700)
        self.db = self.dir / "login.sqlite"
        self.device = "master-runtime-0001"
        self.private = ec.generate_private_key(ec.SECP256R1())
        self.public = self.private.public_key().public_bytes(
            serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
        self.clock = lambda: datetime(2026, 11, 19, 12, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
        self.calls = []

    def producer(self, feed, symbols):
        self.calls.append((feed, symbols))
        return DhanReadBatch("dhan", symbols, {
            s: {"price": 100.0, "observed_at": 1795069800.0}
            for s in symbols
        }, len(self.calls), 1795069800.0)

    def build(self):
        return create_oracle_v2_runtime(
            db_path=self.db, master_device_id=self.device,
            master_public_der=self.public, pairing_key="p" * 40,
            selected_equities=("TCS",), transport=self.producer,
            clock=self.clock, monotonic=lambda: 10)

    def test_no_self_enrollment_and_private_dir_required(self):
        with self.assertRaises(ValueError):
            self.build()
        sessions = DurableDeviceSessions(self.db)
        self.db.chmod(0o600)
        with self.assertRaises(ValueError):
            self.build()
        sessions.bootstrap(self.device, authorize_bootstrap=lambda x: x == self.device)
        self.dir.chmod(0o755)
        with self.assertRaises(ValueError):
            self.build()
        self.dir.chmod(0o700)

    def test_signed_p256_only_and_read_only_routes(self):
        sessions = DurableDeviceSessions(self.db)
        sessions.bootstrap(self.device, authorize_bootstrap=lambda x: x == self.device)
        self.db.chmod(0o600)
        client = TestClient(self.build())
        self.assertEqual(client.get("/v2-pilot/quotes").status_code, 401)
        self.assertEqual(self.calls, [])
        challenge = client.post("/v2-pilot/auth/challenge",
                                json={"device_id": self.device})
        self.assertEqual(challenge.status_code, 200)
        nonce = challenge.json()["challenge"]
        signature = self.private.sign(
            P256ChallengeVerifier.signed_message(self.device, nonce),
            ec.ECDSA(hashes.SHA256()))
        login = client.post("/v2-pilot/auth/login", json={
            "device_id": self.device, "challenge": nonce,
            "signature": encode_b64(signature)})
        self.assertEqual(login.status_code, 200)
        headers = {"Authorization": "Bearer " + login.json()["device_bearer"]}
        self.assertEqual(client.get("/v2-pilot/quotes", headers=headers).status_code, 200)
        self.assertEqual(self.calls[0], ("quotes", ("TCS",)))
        self.assertEqual(client.get("/v2-pilot/orders", headers=headers).status_code, 404)
        self.assertEqual(client.post("/v2-pilot/order", headers=headers).status_code, 404)


    def test_operator_only_evidence_transport_reaches_signed_oracle_app(self):
        import time
        from pilot_v2.oracle_evidence_lane import DhanEvidenceBatch
        sessions = DurableDeviceSessions(self.db)
        sessions.bootstrap(self.device, authorize_bootstrap=lambda x: x == self.device)
        self.db.chmod(0o600)
        calls = []

        def private_collector():
            calls.append(1)
            return DhanEvidenceBatch("dhan", len(calls), time.time(), [
                {"kind": "expiries", "symbol": "NIFTY", "revision": len(calls),
                 "available": ["2026-11-26"]}])
        client = TestClient(create_oracle_v2_runtime(
            db_path=self.db, master_device_id=self.device,
            master_public_der=self.public, pairing_key="p" * 40,
            selected_equities=("TCS",), transport=self.producer,
            evidence_transport=private_collector,
            clock=self.clock, monotonic=lambda: 10))

        self.assertEqual(client.get("/v2-pilot/evidence").status_code, 401)
        self.assertEqual(calls, [])
        challenge = client.post("/v2-pilot/auth/challenge",
                                json={"device_id": self.device}).json()["challenge"]
        signature = self.private.sign(
            P256ChallengeVerifier.signed_message(self.device, challenge),
            ec.ECDSA(hashes.SHA256()))
        result = client.post("/v2-pilot/auth/login", json={
            "device_id": self.device, "challenge": challenge,
            "signature": encode_b64(signature)})
        self.assertEqual(result.status_code, 200)
        headers = {"Authorization": "Bearer " + result.json()["device_bearer"]}
        response = client.get("/v2-pilot/evidence", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["events"][0]["symbol"], "NIFTY")
        self.assertEqual(len(calls), 1)
        self.assertEqual(client.get("/v2-pilot/evidence",
                                    headers=headers).status_code, 200)
        self.assertEqual(len(calls), 1)  # Shared cached evidence.
        self.assertEqual(client.get("/v2-pilot/indices",
                                    headers=headers).status_code, 503)
        self.assertEqual(self.calls, [])  # One shared read budget, no fanout.
        self.assertEqual(client.post("/v2-pilot/auth/logout",
                                     headers=headers).status_code, 200)
        self.assertEqual(client.get("/v2-pilot/evidence",
                                    headers=headers).status_code, 403)

    def test_operator_evidence_is_absent_by_default(self):
        sessions = DurableDeviceSessions(self.db)
        sessions.bootstrap(self.device, authorize_bootstrap=lambda x: x == self.device)
        self.db.chmod(0o600)
        with self.assertRaises(ValueError):
            create_oracle_v2_runtime(
                db_path=self.db, master_device_id=self.device,
                master_public_der=self.public, pairing_key="p" * 40,
                selected_equities=(), transport=self.producer,
                evidence_transport=object(), clock=self.clock,
                monotonic=lambda: 10)
        client = TestClient(self.build())
        self.assertEqual(client.get("/v2-pilot/evidence").status_code, 401)


if __name__ == "__main__":
    unittest.main()
