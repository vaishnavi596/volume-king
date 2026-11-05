"""Gateway contract/security regression tests, entirely offline."""
import asyncio
import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from fastapi.testclient import TestClient
from backend.server import create_app
from market_feed import FeedError, SessionExpired
from server_feed import NoRedirect, ServerAngelFeed, server_origin

PAIR = "owner-access-key-" * 3
LOGIN = dict(api_key="BROKER_PRIVATE_KEY", client_code="OWNER", pin="SECRET_PIN", totp="123456")


class FakeFeed:
    connected = False
    def __init__(self): self.calls = []
    def connect(self, *args): self.connected = True
    def disconnect(self): self.connected = False
    def history(self, *args):
        self.calls.append(args)
        return {"source": "Angel One", "price": 100, "bars": [[123, 99, 101, 98, 100, 10]]}
    def expiries(self, symbol): return ["2026-12-01"]
    def option_chain(self, *args): return {"rows": [{"premium": 80, "lot_size": 25}]}
    def option_history(self, *args): return [[123, 80, 82, 79, 81, 10]]


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.now = [100.0]
        self.feed = FakeFeed()
        self.client = TestClient(create_app(PAIR, self.feed, lambda: self.now[0]))
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def login(self):
        response = self.client.post("/v1/login", json=LOGIN, headers={"X-BotKing-Key": PAIR})
        self.assertEqual(response.status_code, 200, response.text)
        return {"Authorization": "Bearer " + response.json()["session"]}

    def test_health_has_no_secrets_and_orders_are_absent(self):
        self.assertFalse(self.client.get("/health").json()["live_orders_enabled"])
        self.assertEqual(self.client.post("/v1/orders", json={}).status_code, 404)
        self.assertEqual(self.client.get("/docs").status_code, 404)

    def test_owner_key_required_before_broker_login(self):
        response = self.client.post("/v1/login", json=LOGIN)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.feed.connected)
        with self.assertRaises(RuntimeError): create_app("short")

    def test_validation_never_echoes_secrets(self):
        response = self.client.post("/v1/login", json={"api_key": "PRIVATE"}, headers={"X-BotKing-Key": PAIR})
        self.assertEqual(response.status_code, 422)
        self.assertNotIn("PRIVATE", response.text)

    def test_protected_market_routes_and_no_broker_token_in_response(self):
        body = dict(symbol="NIFTY", interval="5m", period="5d")
        self.assertEqual(self.client.post("/v1/history", json=body).status_code, 401)
        headers = self.login()
        response = self.client.post("/v1/history", json=body, headers=headers)
        self.assertEqual(response.json()["price"], 100)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(self.client.post("/v1/expiries", json={"symbol": "NIFTY"}, headers=headers).json(), ["2026-12-01"])
        self.assertEqual(self.client.post("/v1/options", json=dict(symbol="NIFTY", expiry="2026-12-01", spot=24000), headers=headers).status_code, 200)
        self.assertEqual(self.client.post("/v1/option-history", json=dict(symbol="NIFTY", expiry="2026-12-01", strike=24000, side="CE"), headers=headers).status_code, 200)
        self.assertNotIn("BROKER_PRIVATE_KEY", json.dumps(response.json()))

    def test_expiry_relogin_and_logout_invalidate_sessions(self):
        body = dict(symbol="NIFTY")
        old = self.login()
        new = self.login()
        self.assertEqual(self.client.post("/v1/expiries", json=body, headers=old).status_code, 401)
        # Gateway v2.3 idle expiry is two hours, not the old 30 minutes.
        self.now[0] += 3600
        self.assertEqual(self.client.post("/v1/expiries", json=body, headers=new).status_code, 200)
        self.now[0] += 7201
        self.assertEqual(self.client.post("/v1/expiries", json=body, headers=new).status_code, 401)
        self.assertFalse(self.feed.connected)
        new = self.login()
        self.assertEqual(self.client.post("/v1/logout", json={}, headers=new).status_code, 200)
        self.assertEqual(self.client.post("/v1/expiries", json=body, headers=new).status_code, 401)

    def test_broker_failure_is_sanitized_and_expired_session_is_revoked(self):
        headers = self.login()
        with patch.object(self.feed, "expiries", side_effect=RuntimeError("JWT_PRIVATE")):
            response = self.client.post("/v1/expiries", json={"symbol": "NIFTY"}, headers=headers)
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("JWT_PRIVATE", response.text)
        with patch.object(self.feed, "expiries", side_effect=SessionExpired("PRIVATE")):
            self.assertEqual(self.client.post("/v1/expiries", json={"symbol": "NIFTY"}, headers=headers).status_code, 401)
        self.assertFalse(self.feed.connected)

    def test_login_rate_limit_and_body_limit(self):
        for _ in range(5): self.login()
        self.assertEqual(self.client.post("/v1/login", json=LOGIN, headers={"X-BotKing-Key": PAIR}).status_code, 429)
        self.assertEqual(self.client.post("/v1/login", content="x" * 9000).status_code, 413)

    def test_app_transport_end_to_end(self):
        client = self.client
        class Response(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *args): self.close()
        class Opener:
            def open(self, request, timeout):
                response = client.post(request.full_url.replace("https://owner.example", ""),
                                       content=request.data, headers=dict(request.header_items()))
                if response.status_code >= 400:
                    raise urllib.error.HTTPError(request.full_url, response.status_code, "failure", {}, None)
                return Response(response.content)
        feed = ServerAngelFeed()
        with patch("urllib.request.build_opener", return_value=Opener()), patch("urllib.request.urlopen", side_effect=AssertionError("Direct broker call forbidden")):
            feed.connect(*LOGIN.values(), "https://owner.example", PAIR)
            self.assertTrue(feed.connected)
            self.assertFalse(feed.key)
            self.assertEqual(feed.history("NIFTY", "5m", "5d")["price"], 100)
            self.assertEqual(feed.expiries("NIFTY"), ["2026-12-01"])
            self.assertEqual(feed.option_chain("NIFTY", "2026-12-01", 24000)["rows"][0]["premium"], 80)
            self.assertEqual(len(feed.option_history("NIFTY", "2026-12-01", 24000, "CE")), 1)
            feed.revoke()
            self.assertFalse(feed.connected)
            self.assertFalse(self.feed.connected)

    def test_origins_and_redirects_rejected(self):
        for value in ("http://owner.example", "https://owner.example/path", "https://user:pass@owner.example", "https://owner.example?key=x", "https://owner.example:8000"):
            with self.assertRaises(FeedError): server_origin(value)
        self.assertEqual(server_origin("https://owner.example/"), "https://owner.example")
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, "", {}, "https://elsewhere.example"))

    def test_ui_requires_trust_and_never_saves_server_key(self):
        from test_audit import start
        _, values = start({"scanner_live": False})
        values["api_url"].value = "https://owner.example"
        values["server_access"].value = "PRIVATE_SERVER_KEY"
        with patch.object(values["angel_feed"], "connect") as connect:
            asyncio.run(values["connect_angel"]())
            connect.assert_not_called()
        values["save_settings"](None)
        self.assertNotIn("PRIVATE_SERVER_KEY", json.dumps(values["prefs"]))
        self.assertNotIn("PRIVATE_SERVER_KEY", json.dumps(values["backup_payload"]()))
