"""One app entry, one gateway, one read pipeline; offline auth-isolation tests."""
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from pilot_v2.atomic_verified_login import AtomicVerifiedLogin
from pilot_v2.device_verifier import P256ChallengeVerifier, encode_b64
from pilot_v2.durable_challenges import DurableP256ChallengeVerifier
from pilot_v2.durable_device_sessions import DurableDeviceSessions
from pilot_v2.internal_dhan_read_port import DhanReadBatch, InternalDhanReadPort
from pilot_v2.unified_data_pipeline import V2UnifiedReadPipeline
from pilot_v2.unified_gateway_app import create_v2_unified_app

NOW = 1800000000
IST = ZoneInfo("Asia/Kolkata")


class UnifiedGatewayAcceptance(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        db = Path(tmp.name) / "auth.db"
        self.device = "master-v2-unified-0001"
        self.private = ec.generate_private_key(ec.SECP256R1())
        pub = self.private.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo)
        sessions = DurableDeviceSessions(db)
        sessions.bootstrap(self.device, authorize_bootstrap=lambda _: True)
        verifier = DurableP256ChallengeVerifier(db, {self.device: pub})
        login = AtomicVerifiedLogin(verifier, sessions)
        self.calls = []

        def transport(feed, symbols):
            self.calls.append((feed, symbols))
            return DhanReadBatch(
                "dhan", symbols,
                {s: {"price": 101, "observed_at": NOW} for s in symbols},
                len(self.calls), NOW)

        port = InternalDhanReadPort(
            transport=transport, selected_equities=("RELIANCE",),
            clock=lambda: NOW)
        self.pipeline = V2UnifiedReadPipeline(
            read_port=port,
            clock=lambda: datetime(2026, 11, 19, 11, 0, tzinfo=IST),
            monotonic=lambda: 10)
        self.client = TestClient(create_v2_unified_app(
            verified_login=login, data_pipeline=self.pipeline))

    def signed_bearer(self):
        r = self.client.post("/v2-pilot/auth/challenge",
                             json={"device_id": self.device})
        self.assertEqual(r.status_code, 200)
        nonce = r.json()["challenge"]
        signature = self.private.sign(
            P256ChallengeVerifier.signed_message(self.device, nonce),
            ec.ECDSA(hashes.SHA256()))
        r = self.client.post("/v2-pilot/auth/login",
                             json={"device_id": self.device, "challenge": nonce,
                                   "signature": encode_b64(signature)})
        self.assertEqual(r.status_code, 200)
        return r.json()["device_bearer"]

    def test_provider_never_called_before_signed_login(self):
        self.assertEqual(self.client.get("/v2-pilot/quotes").status_code, 401)
        self.assertEqual(self.client.get("/v2-pilot/indices",
                                        headers={"Authorization": "Bearer " + "x" * 48}
                                        ).status_code, 403)
        self.assertEqual(self.calls, [])

    def test_verified_login_serves_both_feeds_one_app(self):
        bearer = self.signed_bearer()
        headers = {"Authorization": "Bearer " + bearer}
        q = self.client.get("/v2-pilot/quotes", headers=headers)
        i = self.client.get("/v2-pilot/indices", headers=headers)
        self.assertEqual(q.status_code, 200)
        self.assertEqual(i.status_code, 200)
        self.assertEqual(set(i.json()["quotes"]), {"NIFTY", "BANKNIFTY", "SENSEX"})
        self.assertEqual(set(q.json()["quotes"]), {"RELIANCE"})
        self.assertEqual(len(self.calls), 2)
        self.assertFalse(q.json()["quotes"]["RELIANCE"]["live_verified"])

    def test_missing_transport_denied_as_503(self):
        bearer = self.signed_bearer()
        self.pipeline._port._transport = lambda *_: (_ for _ in ()).throw(OSError())
        r = self.client.get("/v2-pilot/quotes",
                            headers={"Authorization": "Bearer " + bearer})
        self.assertEqual(r.status_code, 503)
        self.assertEqual(self.calls, [])

    def test_factory_fail_closed(self):
        with self.assertRaises(ValueError):
            create_v2_unified_app(verified_login=None, data_pipeline=self.pipeline)
        with self.assertRaises(ValueError):
            create_v2_unified_app(verified_login=None, data_pipeline=None)


if __name__ == "__main__":
    unittest.main()
