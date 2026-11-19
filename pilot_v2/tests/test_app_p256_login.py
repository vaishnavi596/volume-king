"""Offline P-256 signed login over a fake HTTPS bridge, no Oracle calls."""
import json
import sys
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from urllib.parse import urlsplit
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from app_p256_login import V2P256LoginHTTPSClient
from app_device_reader_slot import DeviceReaderSlot
from secure_https_reader import FeedError, V2ReadonlyHTTPSReader
from pilot_v2.auth_http import create_pilot_auth_app
from pilot_v2.atomic_verified_login import AtomicVerifiedLogin
from pilot_v2.durable_challenges import DurableP256ChallengeVerifier
from pilot_v2.durable_device_sessions import DurableDeviceSessions

DEVICE = "master_device_000001"
ORIGIN = "https://v2.example.test"


class BridgedResponse:
    def __init__(self, url, result):
        self.url = url
        self.status = result.status_code
        self.data = result.content
        self.offset = 0
        self.headers = Message()
        for name, value in result.headers.items():
            self.headers[name] = value

    def geturl(self):
        return self.url

    def read(self, length):
        block = self.data[self.offset:self.offset + length]
        self.offset += len(block)
        return block

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class HTTPSBridge:
    def __init__(self, client):
        self.client = client
        self.calls = []

    def open(self, request, timeout):
        self.calls.append((request.full_url, request.get_method()))
        path = urlsplit(request.full_url).path
        result = self.client.request(
            request.get_method(), path, content=request.data,
            headers={"content-type": request.get_header("Content-type"),
                     "accept": "application/json"})
        return BridgedResponse(request.full_url, result)


class P256AndroidLoginContractTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / "test-auth.db"
        self.key = ec.generate_private_key(ec.SECP256R1())
        public = self.key.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo)
        sessions = DurableDeviceSessions(path, clock=lambda: 1000.)
        sessions.bootstrap(DEVICE, authorize_bootstrap=lambda d: d == DEVICE)
        verifier = DurableP256ChallengeVerifier(
            path, {DEVICE: public}, clock=lambda: 1000.)
        self.sessions = sessions
        self.client = TestClient(create_pilot_auth_app(
            enabled=True,
            login=AtomicVerifiedLogin(verifier, sessions),
            rate_gate=lambda request, action: True),
            base_url=ORIGIN)
        self.bridge = HTTPSBridge(self.client)

    def make_login(self, signer=None):
        callback = signer or (lambda message:
            self.key.sign(message, ec.ECDSA(hashes.SHA256())))
        return V2P256LoginHTTPSClient(
            ORIGIN, DEVICE, callback, opener=self.bridge)

    def test_real_signed_challenge_contract_returns_readonly_reader(self):
        reader = self.make_login().login()
        self.assertIsInstance(reader, V2ReadonlyHTTPSReader)
        self.assertTrue(reader.session_active)
        self.assertEqual(self.bridge.calls, [
            (ORIGIN + "/v2-pilot/auth/challenge", "POST"),
            (ORIGIN + "/v2-pilot/auth/login", "POST")])
        self.assertNotIn("device_bearer", repr(reader))
        self.assertFalse(hasattr(reader, "place_order"))

    def test_wrong_key_and_signer_failure_leave_no_reader(self):
        other_key = ec.generate_private_key(ec.SECP256R1())
        def wrong(message):
            return other_key.sign(message, ec.ECDSA(hashes.SHA256()))
        with self.assertRaises(FeedError):
            self.make_login(wrong).login()
        with self.assertRaises(FeedError) as err:
            self.make_login(lambda message: (_ for _ in ()).throw(
                ValueError("my-private-key-name"))).login()
        self.assertNotIn("my-private-key-name", str(err.exception))
        self.assertNotIn("device_bearer", str(err.exception))

    def test_single_reader_slot_rotates_only_after_real_signed_login(self):
        slot = DeviceReaderSlot()
        with self.assertRaises(FeedError):
            slot.active_reader()
        with self.assertRaises(FeedError):
            slot.sign_in("untrusted-bearer")
        self.assertEqual(self.bridge.calls, [])
        self.assertTrue(slot.sign_in(self.make_login()))
        first = slot.active_reader()
        self.assertTrue(first.session_active)
        self.assertTrue(slot.sign_in(self.make_login()))
        self.assertFalse(first.session_active)
        self.assertTrue(slot.active_reader().session_active)
        slot.clear()
        self.assertIsNone(slot.reader)
        with self.assertRaises(FeedError):
            slot.active_reader()

    def test_bad_signed_relogin_invalidates_old_reader_atomically(self):
        slot = DeviceReaderSlot()
        slot.sign_in(self.make_login())
        first = slot.active_reader()
        wrong_key = ec.generate_private_key(ec.SECP256R1())
        def bad_signer(message):
            return wrong_key.sign(message, ec.ECDSA(hashes.SHA256()))
        with self.assertRaises(FeedError):
            slot.sign_in(self.make_login(bad_signer))
        self.assertFalse(first.session_active)
        self.assertIsNone(slot.reader)
        with self.assertRaises(FeedError):
            slot.active_reader()

    def test_invalid_origin_device_and_signer_fail_before_any_http(self):
        for origin in ("http://v2.example.test", "https://user@v2.example.test"):
            with self.subTest(origin=origin), self.assertRaises(FeedError):
                V2P256LoginHTTPSClient(origin, DEVICE, self.key.sign,
                                       opener=self.bridge)
        for device in ("TCS", "", "bad/device", "a" * 129):
            with self.subTest(device=device), self.assertRaises(FeedError):
                V2P256LoginHTTPSClient(ORIGIN, device, self.key.sign,
                                       opener=self.bridge)
        self.assertEqual(self.bridge.calls, [])

    def test_unapproved_device_never_receives_a_bearer(self):
        unknown = V2P256LoginHTTPSClient(
            ORIGIN, "delegate_unknown_00001", lambda message: b"sigbytes",
            opener=self.bridge)
        with self.assertRaises(FeedError):
            unknown.login()
        self.assertEqual(len(self.bridge.calls), 1)


if __name__ == "__main__":
    unittest.main()
