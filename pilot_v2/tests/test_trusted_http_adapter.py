"""Offline end-to-end P-256 HTTP adapter regression, synthetic data NEVER live."""
import tempfile
from pathlib import Path
import unittest

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from pilot_v2.atomic_verified_login import AtomicVerifiedLogin
from pilot_v2.durable_challenges import DurableP256ChallengeVerifier
from pilot_v2.durable_device_sessions import DurableDeviceSessions
from pilot_v2.device_verifier import P256ChallengeVerifier, encode_b64
from pilot_v2.trusted_http_adapter import create_trusted_app


class TrustedAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        db = Path(self.temp.name) / "v2-only-test.db"
        self.device = "master-device-v2-test"
        self.key = ec.generate_private_key(ec.SECP256R1())
        pub = self.key.public_key().public_bytes(
            serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
        sessions = DurableDeviceSessions(db)
        sessions.bootstrap(self.device, authorize_bootstrap=lambda _: True)
        verifier = DurableP256ChallengeVerifier(db, {self.device: pub})
        self.login = AtomicVerifiedLogin(verifier, sessions)
        self.provider_calls = []

        def provider(device, feed):
            self.provider_calls.append((device, feed))
            return {
                "protocol": "botking-v2-readonly", "schema_version": 1,
                "source": "dhan", "freshness": "unverified",
                "live_orders_enabled": False, "revision": 1,
                "quotes": {"RELIANCE": {
                    "price": 100.0, "freshness": "unverified",
                    "live_verified": False, "revision": 1}}
            }
        self.client = TestClient(create_trusted_app(login=self.login,
                                                     snapshot_provider=provider))

    def signed_login(self):
        challenge = self.client.post("/v2-pilot/auth/challenge",
                                     json={"device_id": self.device})
        self.assertEqual(challenge.status_code, 200)
        self.assertEqual(challenge.headers.get("cache-control"), "no-store")
        nonce = challenge.json()["challenge"]
        signed = self.key.sign(P256ChallengeVerifier.signed_message(self.device, nonce),
                               ec.ECDSA(hashes.SHA256()))
        proof = {"device_id": self.device, "challenge": nonce,
                 "signature": encode_b64(signed)}
        return proof

    def test_real_signature_mock_snapshot_and_replay_denied(self):
        proof = self.signed_login()
        r = self.client.post("/v2-pilot/auth/login", json=proof)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers.get("cache-control"), "no-store")
        token = r.json()["device_bearer"]
        self.assertEqual(self.client.post("/v2-pilot/auth/login",
                                          json=proof).status_code, 403)
        result = self.client.get("/v2-pilot/quotes",
                                 headers={"Authorization": "Bearer " + token})
        self.assertEqual(result.status_code, 200)
        self.assertFalse(result.json()["quotes"]["RELIANCE"]["live_verified"])
        self.assertEqual(self.provider_calls, [(self.device, "quotes")])

    def test_missing_bearer_denied_before_provider(self):
        self.assertEqual(self.client.get("/v2-pilot/indices").status_code, 401)
        self.assertEqual(self.provider_calls, [])

    def test_unknown_device_never_mints_nonce(self):
        r = self.client.post("/v2-pilot/auth/challenge",
                             json={"device_id": "unknown-device-not-authorized"})
        self.assertEqual(r.status_code, 403)

    def test_bogus_signature_denied_and_consumed(self):
        proof = self.signed_login()
        proof["signature"] = encode_b64(b"bogus")
        self.assertEqual(self.client.post("/v2-pilot/auth/login",
                                          json=proof).status_code, 403)
        self.assertEqual(self.provider_calls, [])

    def test_malformed_input_and_no_orders(self):
        self.assertEqual(self.client.post("/v2-pilot/auth/login",
                                          content=b"x" * 1025).status_code, 413)
        self.assertEqual(self.client.get("/v2-pilot/orders").status_code, 404)

    def test_factory_rejects_untrusted_login(self):
        with self.assertRaises(ValueError):
            create_trusted_app(login=object(), snapshot_provider=lambda *_: {})


if __name__ == "__main__":
    unittest.main()
