"""One full OFFLINE P-256 login → protected quote reads → expiry test.

Both FastAPI shells are disabled by default outside this TestClient fixture.
No network, Android Keystore, token logging, Oracle or real Dhan connection.
"""
import sys
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from urllib.parse import urlsplit

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "android_app" / "src"))
from app_device_reader_slot import DeviceReaderSlot
from app_p256_login import V2P256LoginHTTPSClient
from feed_inbox import DeviceFeedInbox, FeedError
from pilot_v2.api_contract import make_snapshot
from pilot_v2.atomic_verified_login import AtomicVerifiedLogin
from pilot_v2.auth_http import create_pilot_auth_app
from pilot_v2.durable_challenges import DurableP256ChallengeVerifier
from pilot_v2.durable_device_sessions import DurableDeviceSessions
from pilot_v2.http_gateway import create_pilot_app

ORIGIN = "https://v2.example.test"
MASTER = "master_device_000001"


class BridgeResponse:
    def __init__(self, url, response):
        self.url = url
        self.status = response.status_code
        self.raw = response.content
        self.position = 0
        self.headers = Message()
        for name, value in response.headers.items():
            self.headers[name] = value

    def geturl(self):
        return self.url

    def read(self, n):
        part = self.raw[self.position:self.position + n]
        self.position += len(part)
        return part

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class LocalHTTPSBridge:
    def __init__(self, auth, feed):
        self.auth = auth
        self.feed = feed
        self.calls = []

    def open(self, request, timeout):
        path = urlsplit(request.full_url).path
        client = self.auth if path.startswith("/v2-pilot/auth/") else self.feed
        headers = {"accept": "application/json"}
        token = request.get_header("Authorization")
        if token is not None:
            headers["authorization"] = token
        if request.data is not None:
            headers["content-type"] = request.get_header("Content-type")
        self.calls.append((request.get_method(), path))
        response = client.request(request.get_method(), path,
                                  content=request.data, headers=headers)
        return BridgeResponse(request.full_url, response)


class ReadonlySignedSessionE2ETests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.clock = [1000.]
        self.key = ec.generate_private_key(ec.SECP256R1())
        public = self.key.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo)
        db_path = Path(folder.name) / "auth.db"
        sessions = DurableDeviceSessions(db_path, clock=lambda: self.clock[0], ttl=60)
        sessions.bootstrap(MASTER, authorize_bootstrap=lambda d: d == MASTER)
        verifier = DurableP256ChallengeVerifier(
            db_path, {MASTER: public}, clock=lambda: self.clock[0])
        auth_app = create_pilot_auth_app(
            enabled=True, login=AtomicVerifiedLogin(verifier, sessions),
            rate_gate=lambda request, action: True)
        def provider(device, feed):
            self.assertEqual(device, MASTER)
            if feed == "indices":
                return make_snapshot(7, {"NIFTY": self.row(25000, 7)})
            return make_snapshot(3, {"TCS": self.row(100, 3)})
        feeds_app = create_pilot_app(
            enabled=True, sessions=sessions, snapshot_provider=provider)
        self.bridge = LocalHTTPSBridge(
            TestClient(auth_app, base_url=ORIGIN),
            TestClient(feeds_app, base_url=ORIGIN))
        self.slot = DeviceReaderSlot()
        self.inbox = DeviceFeedInbox()

    @staticmethod
    def row(price, revision):
        return {"price": price, "freshness": "unverified",
                "live_verified": False, "revision": revision}

    def test_login_then_two_independent_feeds_then_expiry_freezes_last_good(self):
        login = V2P256LoginHTTPSClient(
            ORIGIN, MASTER,
            lambda message: self.key.sign(message, ec.ECDSA(hashes.SHA256())),
            opener=self.bridge)
        self.assertTrue(self.slot.sign_in(login))
        reader = self.slot.active_reader()
        self.assertTrue(reader.refresh(self.inbox, "indices", selected_equities=()))
        self.assertTrue(reader.refresh(self.inbox, "quotes", selected_equities=("TCS",)))
        self.assertEqual(self.inbox.revision_for("indices"), 7)
        self.assertEqual(self.inbox.revision_for("quotes"), 3)
        self.assertEqual(self.inbox.visible("NIFTY", ())["price"], 25000)
        self.assertEqual(self.inbox.visible("TCS", ("TCS",))["price"], 100)
        self.assertFalse(reader.refresh(self.inbox, "quotes", selected_equities=("TCS",)))
        self.clock[0] += 60
        with self.assertRaises(FeedError):
            reader.refresh(self.inbox, "indices")
        self.assertFalse(reader.session_active)
        calls = len(self.bridge.calls)
        with self.assertRaises(FeedError):
            reader.refresh(self.inbox, "quotes", selected_equities=("TCS",))
        self.assertEqual(len(self.bridge.calls), calls)
        self.assertEqual(self.inbox.visible("TCS", ("TCS",))["price"], 100)
        self.assertEqual(self.inbox.visible("NIFTY", ())["price"], 25000)

    def test_unapproved_device_not_allowed_a_read(self):
        stranger = V2P256LoginHTTPSClient(
            ORIGIN, "unapproved_device_0001",
            lambda message: self.key.sign(message, ec.ECDSA(hashes.SHA256())),
            opener=self.bridge)
        with self.assertRaises(FeedError):
            self.slot.sign_in(stranger)
        self.assertIsNone(self.slot.reader)
        self.assertEqual(self.bridge.calls, [
            ("POST", "/v2-pilot/auth/challenge")])


if __name__ == "__main__":
    unittest.main()
