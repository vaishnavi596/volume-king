"""V2 FT1 simulated HTTPS challenge-to-session API, no Oracle requests."""
import tempfile
import unittest
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from pilot_v2.atomic_verified_login import AtomicVerifiedLogin
from pilot_v2.auth_http import create_pilot_auth_app
from pilot_v2.device_sessions import VerifiedDevice, SessionDenied
from pilot_v2.device_verifier import P256ChallengeVerifier, encode_b64
from pilot_v2.durable_challenges import DurableP256ChallengeVerifier
from pilot_v2.durable_device_sessions import DurableDeviceSessions

MASTER = "master_device_000001"
SECOND = "second_device_00001"


class PilotAuthHTTPTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.now = [1000.0]
        path = Path(tmp.name) / "auth.db"
        self.key = ec.generate_private_key(ec.SECP256R1())
        public = self.key.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo)
        self.sessions = DurableDeviceSessions(path, clock=lambda: self.now[0])
        self.sessions.bootstrap(MASTER, authorize_bootstrap=lambda device: device == MASTER)
        self.verifier = DurableP256ChallengeVerifier(
            path, {MASTER: public}, clock=lambda: self.now[0])
        self.gateway = AtomicVerifiedLogin(self.verifier, self.sessions)
        self.allowed = [True]
        def rate_gate(request, action):
            return self.allowed[0] and action in ("challenge", "login")
        self.app = create_pilot_auth_app(
            enabled=True, login=self.gateway, rate_gate=rate_gate)
        self.https = TestClient(self.app, base_url="https://v2.example.test")

    def post(self, path, data, *, client=None):
        return (client or self.https).post("/v2-pilot/auth/" + path, json=data)

    def sign(self, nonce, key=None):
        private = key or self.key
        signed = P256ChallengeVerifier.signed_message(MASTER, nonce)
        return encode_b64(private.sign(signed, ec.ECDSA(hashes.SHA256())))

    def test_feature_flag_off_and_missing_dependencies_fail_closed(self):
        disabled = TestClient(create_pilot_auth_app(), base_url="https://v2.example.test")
        self.assertEqual(disabled.post("/v2-pilot/auth/challenge",
                                       json={"device_id": MASTER}).status_code, 404)
        with self.assertRaises(ValueError):
            create_pilot_auth_app(enabled=True, login=self.gateway)
        with self.assertRaises(ValueError):
            create_pilot_auth_app(enabled=True, rate_gate=lambda req, action: True)

    def test_only_https_rate_limited_owner_signed_proof_issues_bearer(self):
        http = TestClient(self.app, base_url="http://v2.example.test")
        self.assertEqual(self.post("challenge", {"device_id": MASTER},
                                   client=http).status_code, 403)
        self.allowed[0] = False
        self.assertEqual(self.post("challenge", {"device_id": MASTER}).status_code, 429)
        self.allowed[0] = True
        challenge = self.post("challenge", {"device_id": MASTER})
        self.assertEqual(challenge.status_code, 200)
        nonce = challenge.json()["challenge"]
        response = self.post("login", {"device_id": MASTER,
                                       "challenge": nonce,
                                       "signature": self.sign(nonce)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["cache-control"], "no-store")
        bearer = response.json()["device_bearer"]
        self.assertEqual(self.sessions.authorize(bearer, "quotes"), MASTER)
        self.assertEqual(self.sessions.authorize(bearer, "indices"), MASTER)
        self.assertEqual(self.post("login", {"device_id": MASTER,
                                            "challenge": nonce,
                                            "signature": self.sign(nonce)}).status_code, 403)

    def test_forged_signature_and_unknown_device_get_no_session(self):
        self.assertEqual(self.post("challenge", {"device_id": SECOND}).status_code, 403)
        nonce = self.post("challenge", {"device_id": MASTER}).json()["challenge"]
        wrong = ec.generate_private_key(ec.SECP256R1())
        proof = {"device_id": MASTER, "challenge": nonce,
                 "signature": self.sign(nonce, key=wrong)}
        self.assertEqual(self.post("login", proof).status_code, 403)
        self.assertEqual(self.post("login", {**proof,
                         "signature": self.sign(nonce)}).status_code, 403)
        with self.assertRaises(SessionDenied):
            self.sessions.authorize("x" * 64, "quotes")

    def test_oversized_wrong_content_and_extra_fields_do_not_authorize(self):
        self.assertEqual(self.post("challenge", {"device_id": MASTER,
                                                 "admin": True}).status_code, 400)
        self.assertEqual(self.post("login", {"device_id": MASTER}).status_code, 400)
        self.assertEqual(self.https.post("/v2-pilot/auth/challenge",
                                         data="hello", headers={"content-type": "text/plain"}).status_code, 415)
        self.assertEqual(self.https.post("/v2-pilot/auth/challenge",
                                         content="x" * 1100,
                                         headers={"content-type": "application/json"}).status_code, 413)
        self.assertEqual(self.https.post("/v2-pilot/orders").status_code, 404)
        self.assertEqual(self.https.get("/openapi.json").status_code, 404)

    def test_expired_challenge_or_revoked_master_fails_closed(self):
        nonce = self.post("challenge", {"device_id": MASTER}).json()["challenge"]
        self.now[0] += 60
        self.assertEqual(self.post("login", {"device_id": MASTER, "challenge": nonce,
                                            "signature": self.sign(nonce)}).status_code, 403)
        nonce = self.post("challenge", {"device_id": MASTER}).json()["challenge"]
        self.assertEqual(self.post("login", {"device_id": MASTER, "challenge": nonce,
                                            "signature": self.sign(nonce)}).status_code, 200)


if __name__ == "__main__":
    unittest.main()
