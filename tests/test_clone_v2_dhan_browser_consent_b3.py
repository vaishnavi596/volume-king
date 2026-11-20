"""Clone-only Dhan OAuth browser flow: no V1 HTTP calls or live broker orders."""
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from backend.clone_v2_gateway import create_app


class DummyResponse:
    status = 200
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, n):
        return self.payload[:n]


class FakeDhanOpener:
    def __init__(self, client, *, mismatch=False):
        self.client = client
        self.mismatch = mismatch
        self.paths = []
    def open(self, request, timeout=None):
        self.paths.append(request.full_url)
        if "generate-consent" in request.full_url:
            return DummyResponse({"consentAppId":"once-123"})
        if "consumeApp-consent" in request.full_url:
            expiry=(datetime.now(timezone.utc)+timedelta(hours=12)).isoformat()
            return DummyResponse({"accessToken":"f"*40, "dhanClientId":
                                  "other" if self.mismatch else self.client,
                                  "expiryTime":expiry})
        if request.full_url=="https://api.dhan.co/v2/profile":
            return DummyResponse({"dhanClientId":self.client, "dataPlan":"Active"})
        raise AssertionError("Unexpected Dhan URL")


class CloneBrowserConsentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"dhan-token"
        self.path.write_text("stale-token\n")
        self.path.chmod(0o600)
        self.key="q"*40

    def app(self, mismatch=False):
        opener=FakeDhanOpener("owner-client", mismatch=mismatch)
        return TestClient(create_app(
            key_bytes=self.key.encode(),
            consent_config_factory=lambda:(
                "owner-client", "test-app", "private-secret", self.path))), opener

    def test_start_denied_without_ssk_and_missing_configuration(self):
        app, opener=self.app()
        self.assertEqual(app.post("/clone-v2/dhan/start").status_code,403)
        self.assertEqual(app.post("/clone-v2/dhan/start",headers={"X-BotKing-Key":"x"*40}).status_code,403)
        with patch.dict(os.environ, {"BOTKING_CLONE_DHAN_CALLBACK_APPROVED":"0"},clear=False):
            bare=TestClient(create_app(key_bytes=self.key.encode()))
            self.assertEqual(bare.post("/clone-v2/dhan/start",headers={"X-BotKing-Key":self.key}).status_code,503)
        self.assertEqual(opener.paths,[])

    def test_callback_replay_rejected_and_private_token_updated(self):
        app, opener=self.app()
        with patch("backend.clone_v2_gateway.urllib.request.build_opener",return_value=opener):
            result=app.post("/clone-v2/dhan/start",headers={"X-BotKing-Key":self.key})
            self.assertEqual(result.status_code,200)
            self.assertEqual(result.json()["live_orders_enabled"],False)
            self.assertEqual(result.headers["Cache-Control"],"no-store")
            self.assertEqual(result.json()["login_url"],"https://auth.dhan.co/login/consentApp-login?consentAppId=once-123")
            self.assertEqual(app.post("/clone-v2/dhan/start",headers={"X-BotKing-Key":self.key}).status_code,409)
            callback=app.get("/dhan/callback?tokenId=one-time-code")
            self.assertEqual(callback.status_code,200)
            self.assertIn("Dhan login successful",callback.text)
            self.assertEqual(callback.headers["Cache-Control"],"no-store")
            self.assertEqual(self.path.read_text(),"f"*40+"\n")
            self.assertEqual(app.get("/clone-v2/dhan/callback?tokenId=one-time-code").status_code,403)
            self.assertEqual(app.get("/dhan/callback?tokenId=one-time-code").status_code,403)
        self.assertEqual(len(opener.paths),3)
        self.assertTrue(all(x.startswith("https://auth.dhan.co/app/") for x in opener.paths[:2]))
        self.assertEqual(opener.paths[2],"https://api.dhan.co/v2/profile")

    def test_invalid_dhan_account_never_replaces_old_token(self):
        app, opener=self.app(mismatch=True)
        with patch("backend.clone_v2_gateway.urllib.request.build_opener",return_value=opener):
            self.assertEqual(app.post("/clone-v2/dhan/start",headers={"X-BotKing-Key":self.key}).status_code,200)
            self.assertEqual(app.get("/clone-v2/dhan/callback?tokenId=bad").status_code,502)
        self.assertEqual(self.path.read_text(),"stale-token\n")

    def test_existing_v1_callback_handoff_requires_approved_setting(self):
        app, opener=self.app()
        self.assertEqual(app.get("/dhan/callback?tokenId=unrequested").status_code,403)
        with patch.dict(os.environ, {
            "BOTKING_CLONE_DHAN_CALLBACK_APPROVED":"1",
            "BOTKING_CLONE_DHAN_CALLBACK_URL":"https://botkingrajesh.duckdns.org/dhan/callback",
            "BOTKING_CLONE_DHAN_APP_ID":"demo-app",
            "BOTKING_CLONE_DHAN_APP_SECRET":"demo-secret",
            "DHAN_CLIENT_ID":"owner-client",
            "BOTKING_CLONE_DHAN_TOKEN_FILE":str(self.path),
        }):
            # Clone credential policy accepts original URL, not a newly generated app.
            configured=TestClient(create_app(key_bytes=self.key.encode()))
            self.assertEqual(configured.post("/clone-v2/dhan/start").status_code,403)

    def test_unrequested_callback_forbidden(self):
        app,opener=self.app()
        with patch("backend.clone_v2_gateway.urllib.request.build_opener",return_value=opener):
            self.assertEqual(app.get("/clone-v2/dhan/callback?tokenId=unrequested").status_code,403)
        self.assertEqual(opener.paths,[])


if __name__=="__main__":
    unittest.main()
