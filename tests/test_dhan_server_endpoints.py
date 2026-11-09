"""Read-only Dhan endpoint contract tests, with mocked token and upstream."""
import os
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.server import create_app

PAIRING_KEY = "test-only-pairing-key-32-characters-long"

class StubAngel:
    connected = False
    instruments = None
    resolved = {}
    def disconnect(self): pass

class FakeDhan:
    def __init__(self, client, token): pass
    def ltp(self, segment, sid):
        return {"status": "success", "data": {"IDX_I": {"13": {"last_price": 25030.35}}}}
    def intraday(self, payload):
        return {"open": [100, 102], "high": [104, 105], "low": [99, 101],
                "close": [102, 103], "volume": [50, 60],
                "timestamp": [1760000000, 1760000300]}

class DhanEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app(pairing_key=PAIRING_KEY, feed=StubAngel()))
        self.headers = {"X-BotKing-Key": PAIRING_KEY}
        self.env = patch.dict(os.environ, {"DHAN_CLIENT_ID": "test-client"})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_dhan_session_restores_after_server_restart(self):
        class Response:
            def __init__(self, data): self.data = data
            def raise_for_status(self): pass
            def json(self): return self.data

        with tempfile.TemporaryDirectory() as directory:
            session_file = str(Path(directory) / "dhan-session.json")
            credentials = {"DHAN_CLIENT_ID": "test-client",
                           "DHAN_API_KEY": "test-api-key",
                           "DHAN_API_SECRET": "test-api-secret",
                           "DHAN_SESSION_FILE": session_file}
            with patch.dict(os.environ, credentials), \
                 patch("backend.server.requests.post", return_value=Response({"consentAppId": "consent"})), \
                 patch("backend.server.requests.get", return_value=Response({
                     "accessToken": "durable-token", "dhanClientId": "test-client",
                     "expiryTime": "2099-01-01T00:00:00Z"})):
                first = TestClient(create_app(pairing_key=PAIRING_KEY, feed=StubAngel()))
                self.assertEqual(first.post("/dhan/start", headers=self.headers).status_code, 200)
                self.assertEqual(first.get("/dhan/callback?tokenId=token-id").status_code, 200)
                self.assertEqual(Path(session_file).stat().st_mode & 0o077, 0)
                self.assertTrue(Path(session_file).exists())
                restarted = TestClient(create_app(pairing_key=PAIRING_KEY, feed=StubAngel()))
                status = restarted.get("/dhan/status", headers=self.headers).json()
                self.assertTrue(status["authenticated"])
                self.assertEqual(status["token_source"], "oauth_consent")
                self.assertNotIn("durable-token", str(status))

    def test_successful_consent_token_is_used_for_ltp_without_token_file(self):
        class Response:
            def __init__(self, data):
                self.data = data
            def raise_for_status(self): pass
            def json(self): return self.data

        class CaptureDhan(FakeDhan):
            def __init__(self, client, token):
                self.token = token
                self.client = client
            def ltp(self, segment, sid):
                self.__class__.seen_token = self.token
                return super().ltp(segment, sid)

        credentials = {"DHAN_CLIENT_ID": "test-client",
                       "DHAN_API_KEY": "test-api-key",
                       "DHAN_API_SECRET": "test-api-secret"}
        with patch.dict(os.environ, credentials), \
             patch("backend.server.requests.post", return_value=Response({"consentAppId": "consent"})), \
             patch("backend.server.requests.get", return_value=Response({
                 "accessToken": "consent-access-token", "dhanClientId": "test-client",
                 "expiryTime": "2099-01-01T00:00:00Z"})), \
             patch("backend.server.Path.read_text", side_effect=PermissionError), \
             patch("backend.server.DhanFeed", CaptureDhan):
            self.assertEqual(self.client.post("/dhan/start", headers=self.headers).status_code, 200)
            self.assertEqual(self.client.get("/dhan/callback?tokenId=token-id").status_code, 200)
            status = self.client.get("/dhan/status", headers=self.headers).json()
            self.assertTrue(status["authenticated"])
            self.assertEqual(status["token_source"], "oauth_consent")
            self.assertFalse(status["reauthentication_required"])
            self.assertEqual(status["token_validity"], "expiry_checked")
            self.assertFalse(status["renewal_supported"])
            self.assertTrue(status["market_data_configured"])
            response = self.client.post("/dhan/ltp", json={"symbol": "NIFTY"}, headers=self.headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(CaptureDhan.seen_token, "consent-access-token")
            self.assertNotIn("consent-access-token", response.text)

    def test_expired_token_callback_does_not_claim_login_success(self):
        class Response:
            def __init__(self, data): self.data = data
            def raise_for_status(self): pass
            def json(self): return self.data

        with patch.dict(os.environ, {"DHAN_CLIENT_ID": "test-client",
                                      "DHAN_API_KEY": "test-key",
                                      "DHAN_API_SECRET": "test-secret"}), \
             patch("backend.server.requests.post", return_value=Response({"consentAppId": "consent"})), \
             patch("backend.server.requests.get", return_value=Response({
                 "accessToken": "expired-token", "dhanClientId": "test-client",
                 "expiryTime": "2020-01-01T00:00:00Z"})), \
             patch("backend.server.Path.read_text", side_effect=PermissionError):
            self.assertEqual(self.client.post("/dhan/start", headers=self.headers).status_code, 200)
            self.assertEqual(self.client.get("/dhan/callback?tokenId=expired-id").status_code, 502)
            status = self.client.get("/dhan/status", headers=self.headers).json()
            self.assertFalse(status["authenticated"])
            self.assertFalse(status["market_data_configured"])

    def test_dhan_documented_naive_ist_expiry_is_accepted(self):
        class Response:
            def __init__(self, data): self.data = data
            def raise_for_status(self): pass
            def json(self): return self.data

        with patch.dict(os.environ, {"DHAN_CLIENT_ID": "test-client",
                                      "DHAN_API_KEY": "test-key",
                                      "DHAN_API_SECRET": "test-secret"}), \
             patch("backend.server.requests.post", return_value=Response({"consentAppId": "consent"})), \
             patch("backend.server.requests.get", return_value=Response({
                 "accessToken": "ist-consent-token", "dhanClientId": "test-client",
                 "expiryTime": "2099-01-01T12:37:23"})), \
             patch("backend.server.Path.read_text", side_effect=PermissionError):
            self.assertEqual(self.client.post("/dhan/start", headers=self.headers).status_code, 200)
            self.assertEqual(self.client.get("/dhan/callback?tokenId=ist-id").status_code, 200)
            status = self.client.get("/dhan/status", headers=self.headers).json()
            self.assertTrue(status["authenticated"])
            self.assertEqual(status["token_source"], "oauth_consent")
            self.assertEqual(status["token_validity"], "expiry_checked")

    def test_expired_consent_token_is_not_used_for_market_data(self):
        class Response:
            def __init__(self, data): self.data = data
            def raise_for_status(self): pass
            def json(self): return self.data

        with patch.dict(os.environ, {"DHAN_CLIENT_ID": "test-client",
                                      "DHAN_API_KEY": "test-key",
                                      "DHAN_API_SECRET": "test-secret"}), \
             patch("backend.server.requests.post", return_value=Response({"consentAppId": "consent"})), \
             patch("backend.server.requests.get", return_value=Response({
                 "accessToken": "expired-consent-token", "dhanClientId": "test-client",
                 "expiryTime": "2020-01-01T00:00:00Z"})), \
             patch("backend.server.Path.read_text", side_effect=PermissionError), \
             patch("backend.server.DhanFeed") as dhan:
            self.assertEqual(self.client.post("/dhan/start", headers=self.headers).status_code, 200)
            self.assertEqual(self.client.get("/dhan/callback?tokenId=expired-id").status_code, 502)
            status = self.client.get("/dhan/status", headers=self.headers).json()
            self.assertFalse(status["market_data_configured"])
            self.assertFalse(status["authenticated"])
            self.assertEqual(status["token_source"], "none")
            self.assertTrue(status["reauthentication_required"])
            self.assertEqual(status["token_validity"], "missing")
            self.assertEqual(status["expires_at"], "")
            self.assertEqual(self.client.post("/dhan/ltp", json={"symbol": "NIFTY"},
                                              headers=self.headers).status_code, 503)
            dhan.assert_not_called()

    def test_missing_expiry_consent_is_not_trusted_for_market_data(self):
        class Response:
            def __init__(self, data): self.data = data
            def raise_for_status(self): pass
            def json(self): return self.data

        with patch.dict(os.environ, {"DHAN_CLIENT_ID": "test-client",
                                      "DHAN_API_KEY": "test-key",
                                      "DHAN_API_SECRET": "test-secret"}), \
             patch("backend.server.requests.post", return_value=Response({"consentAppId": "consent"})), \
             patch("backend.server.requests.get", return_value=Response({
                 "accessToken": "no-expiry-token", "dhanClientId": "test-client"})), \
             patch("backend.server.Path.read_text", side_effect=PermissionError), \
             patch("backend.server.DhanFeed") as dhan:
            self.assertEqual(self.client.post("/dhan/start", headers=self.headers).status_code, 200)
            self.assertEqual(self.client.get("/dhan/callback?tokenId=missing-expiry").status_code, 502)
            status = self.client.get("/dhan/status", headers=self.headers).json()
            self.assertFalse(status["authenticated"])
            self.assertEqual(status["expires_at"], "")
            self.assertFalse(status["market_data_configured"])
            self.assertEqual(self.client.post("/dhan/ltp", json={"symbol": "NIFTY"},
                                              headers=self.headers).status_code, 503)
            dhan.assert_not_called()

    def test_pairing_required(self):
        self.assertEqual(self.client.post("/dhan/ltp", json={"symbol": "NIFTY"}).status_code, 403)
        self.assertEqual(self.client.post("/dhan/intraday", json={
            "symbol": "NIFTY", "interval": 5, "from_date": "2026-01-01",
            "to_date": "2026-01-02"}).status_code, 403)

    def test_status_distinguishes_server_token_from_consent(self):
        self.assertEqual(self.client.get("/dhan/status").status_code, 403)
        with patch("backend.server.Path.read_text", return_value="test-token"):
            response = self.client.get("/dhan/status", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["market_data_configured"])
        self.assertFalse(response.json()["authenticated"])
        self.assertEqual(response.json()["token_source"], "provisioned_unverified")
        self.assertFalse(response.json()["reauthentication_required"])
        self.assertEqual(response.json()["token_validity"], "unverified")
        self.assertFalse(response.json()["renewal_supported"])
        self.assertFalse(response.json()["live_orders_enabled"])
        self.assertNotIn("test-token", response.text)

    def test_expired_consent_falls_back_to_provisioned_token_without_claiming_login(self):
        class Response:
            def __init__(self, data): self.data = data
            def raise_for_status(self): pass
            def json(self): return self.data

        with patch.dict(os.environ, {"DHAN_CLIENT_ID": "test-client",
                                      "DHAN_API_KEY": "test-key",
                                      "DHAN_API_SECRET": "test-secret"}), \
             patch("backend.server.requests.post", return_value=Response({"consentAppId": "consent"})), \
             patch("backend.server.requests.get", return_value=Response({
                 "accessToken": "expired-consent-token", "dhanClientId": "test-client",
                 "expiryTime": "2020-01-01T00:00:00Z"})), \
             patch("backend.server.Path.read_text", return_value="provisioned-token"):
            self.assertEqual(self.client.post("/dhan/start", headers=self.headers).status_code, 200)
            self.assertEqual(self.client.get("/dhan/callback?tokenId=expired-id").status_code, 502)
            status = self.client.get("/dhan/status", headers=self.headers).json()
            self.assertFalse(status["authenticated"])
            self.assertTrue(status["market_data_configured"])
            self.assertEqual(status["token_source"], "provisioned_unverified")
            self.assertFalse(status["renewal_supported"])
            self.assertEqual(status["expires_at"], "")
            self.assertNotIn("provisioned-token", str(status))

    def test_status_unreadable_token_is_not_configured(self):
        with patch("backend.server.Path.read_text", side_effect=PermissionError):
            response = self.client.get("/dhan/status", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["market_data_configured"])

    def test_unknown_symbol_rejected(self):
        response = self.client.post("/dhan/ltp", json={"symbol": "UNKNOWN"}, headers=self.headers)
        self.assertEqual(response.status_code, 422)

    @patch("backend.server.Path.read_text", return_value="test-token")
    @patch("backend.server.DhanFeed", FakeDhan)
    def test_ltp(self, read_text):
        response = self.client.post("/dhan/ltp", json={"symbol": "NIFTY"}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["ltp"], 25030.35)
        self.assertEqual(response.json()["freshness"], "unverified")
        self.assertFalse(response.json()["live_orders_enabled"])

    @patch("backend.server.Path.read_text", return_value="test-token")
    @patch("backend.server.DhanFeed", FakeDhan)
    def test_candles(self, read_text):
        response = self.client.post("/dhan/intraday", json={
            "symbol": "NIFTY", "interval": 5, "from_date": "2026-01-01",
            "to_date": "2026-01-02"}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["bars"]), 2)
        self.assertEqual(response.json()["freshness"], "historical_unverified")

    @patch("backend.server.Path.read_text", return_value="test-token")
    @patch("backend.server.DhanFeed")
    def test_malformed_candles_rejected(self, feed_class, read_text):
        feed_class.return_value.intraday.return_value = {
            "open": [100], "high": [99], "low": [98],
            "close": [101], "volume": [50], "timestamp": [1760000000]}
        response = self.client.post("/dhan/intraday", json={
            "symbol": "NIFTY", "interval": 5, "from_date": "2026-01-01",
            "to_date": "2026-01-02"}, headers=self.headers)
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("test-token", response.text)

    @patch("backend.server.Path.read_text", side_effect=PermissionError)
    def test_unreadable_token_is_service_unavailable(self, read_text):
        response = self.client.post("/dhan/ltp", json={"symbol": "NIFTY"}, headers=self.headers)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("test-token", response.text)

    def test_invalid_date_range(self):
        response = self.client.post("/dhan/intraday", json={
            "symbol": "NIFTY", "interval": 5, "from_date": "2026-01-01",
            "to_date": "2026-02-01"}, headers=self.headers)
        self.assertEqual(response.status_code, 422)

if __name__ == "__main__":
    unittest.main()
