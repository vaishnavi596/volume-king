"""Offline API router tests. Production app does not include these routes."""
import base64
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.device_auth_api_226 import build_device_auth_router, authorize_readonly_device_session
from backend.device_login_226 import DeviceLoginCoordinator
from backend.device_registry_226 import DeviceRegistry
from backend.device_proof_226 import Ed25519PublicKey


@unittest.skipUnless(Ed25519PublicKey is not None, "cryptography unavailable")
class DeviceApiTests(unittest.TestCase):
    def setUp(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        registry = DeviceRegistry(Path(self.temp.name) / "device.db")
        self.registry = registry
        self.private = Ed25519PrivateKey.generate()
        pub = self.private.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw)
        self.device = "android_owner_device_226"
        registry.enroll_approved_device(
            self.device, base64.urlsafe_b64encode(pub).decode("ascii"),
            owner_approved=True)
        app = FastAPI()
        app.include_router(build_device_auth_router(registry, DeviceLoginCoordinator(registry)))
        self.client = TestClient(app)

    def test_challenge_session_validate(self):
        response = self.client.post("/v2/device/challenge", json={"device_id": self.device})
        self.assertEqual(response.status_code, 200)
        challenge = response.json()["challenge"]
        signature = self.private.sign(
            b"BOTKING226:DEVICE-AUTH:v1:" + base64.urlsafe_b64decode(challenge))
        proof = {"device_id": self.device, "challenge": challenge,
                 "signature": base64.urlsafe_b64encode(signature).decode("ascii")}
        response = self.client.post("/v2/device/session", json=proof)
        self.assertEqual(response.status_code, 200)
        token = response.json()["access_token"]
        response = self.client.post("/v2/device/validate",
                                    json={"device_id": self.device},
                                    headers={"Authorization": "Bearer " + token})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["authenticated"])
        other = self.client.post("/v2/device/validate", json={"device_id": "another_android_device_226"}, headers={"Authorization": "Bearer " + token})
        self.assertEqual(other.status_code, 401)
        self.assertEqual(other.headers.get("cache-control"), "no-store")
        self.assertEqual(self.client.post("/v2/device/validate",
            json={"device_id": self.device, "session_token": token}).status_code, 401)
        self.assertEqual(self.client.post("/v2/device/validate",
            json={"device_id": self.device},
            headers={"Authorization": "Bearer wrong"}).status_code, 401)
        self.assertEqual(self.client.post("/v2/device/session", json=proof).status_code, 403)

    def test_readonly_bearer_validation_and_revocation(self):
        challenge = self.client.post("/v2/device/challenge",
                                     json={"device_id": self.device}).json()["challenge"]
        signature = self.private.sign(
            b"BOTKING226:DEVICE-AUTH:v1:" + base64.urlsafe_b64decode(challenge))
        proof = {"device_id": self.device, "challenge": challenge,
                 "signature": base64.urlsafe_b64encode(signature).decode("ascii")}
        token = self.client.post("/v2/device/session", json=proof).json()["access_token"]
        self.assertTrue(authorize_readonly_device_session(
            self.registry, "Bearer " + token))
        for bad in (None, "bearer " + token, "Bearer " + token + " ",
                    "Bearer " + token + ".", "Bearer wrong"):
            self.assertFalse(authorize_readonly_device_session(self.registry, bad))
        self.registry.revoke_device(self.device)
        self.assertFalse(authorize_readonly_device_session(
            self.registry, "Bearer " + token))

    def test_auth_responses_disable_caching(self):
        challenge = self.client.post("/v2/device/challenge",
                                     json={"device_id": self.device})
        self.assertEqual(challenge.headers.get("cache-control"), "no-store")
        invalid_session = self.client.post("/v2/device/session", json={
            "device_id": self.device, "challenge": "x" * 44,
            "signature": "x" * 96})
        self.assertEqual(invalid_session.headers.get("cache-control"), "no-store")
        self.assertEqual(invalid_session.status_code, 403)
        validation = self.client.post("/v2/device/validate",
                                      json={"device_id": self.device})
        self.assertEqual(validation.headers.get("cache-control"), "no-store")
        self.assertEqual(validation.status_code, 401)
        unknown = self.client.post("/v2/device/challenge", json={"device_id": "unknown_android_device_226"})
        self.assertEqual(unknown.status_code, 403)
        self.assertEqual(unknown.headers.get("cache-control"), "no-store")

    def test_malformed_bearer_header_rejected(self):
        for header in ("Bearer", "bearer abc", "Bearer  ", "Basic abc"):
            with self.subTest(header=header):
                response = self.client.post("/v2/device/validate",
                    json={"device_id": self.device},
                    headers={"Authorization": header})
                self.assertEqual(response.status_code, 401)

    def test_unenrolled_device_rejected(self):
        response = self.client.post("/v2/device/challenge",
                                    json={"device_id": "unknown_android_device_226"})
        self.assertEqual(response.status_code, 403)

    def test_no_public_enrollment_route(self):
        self.assertEqual(self.client.post("/v2/device/enroll", json={}).status_code, 404)


if __name__ == "__main__":
    unittest.main()
