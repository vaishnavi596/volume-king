"""Offline regression: OAuth auth failure may retry a distinct provisioned token once."""
import unittest
from unittest.mock import patch
from pathlib import Path
from fastapi.testclient import TestClient
from backend import server

KEY = "test-only-pairing-key-32-characters-long"


class OAuthFallbackTests(unittest.TestCase):
    def test_ltp_fallback_only_after_auth_error(self):
        seen = []
        class FakeDhan:
            def __init__(self, client, token):
                self.token = token
            def ltp(self, segment, sid):
                seen.append(self.token)
                if self.token == "oauth-test":
                    raise server.DhanFeedError("Dhan token expired or data access not entitled")
                return {"status": "success", "data": {"IDX_I": {"13": {"last_price": 25030.35}}}}
        with patch.dict("os.environ", {"DHAN_CLIENT_ID": "test-client"}), \
             patch.object(server, "DhanFeed", FakeDhan), \
             patch.object(Path, "read_text", return_value="provisioned-test"):
            app = server.create_app(pairing_key=KEY)
            # Inject a valid OAuth session using the closure's session object.
            for cell in app.router.routes:
                if getattr(cell, "path", "") == "/dhan/status":
                    status_fn = cell.endpoint
                    break
            session = next(c.cell_contents for c in status_fn.__closure__
                           if isinstance(c.cell_contents, dict)
                           and "access_token" in c.cell_contents)
            session.update(access_token="oauth-test", expires_at="2099-01-01T00:00:00Z")
            response = TestClient(app).post("/dhan/ltp", json={"symbol": "NIFTY"},
                                            headers={"X-BotKing-Key": KEY})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(seen, ["oauth-test", "provisioned-test"])
        self.assertFalse(response.json()["live_orders_enabled"])

    def test_rate_limit_never_falls_back(self):
        seen = []
        class FakeDhan:
            def __init__(self, client, token):
                seen.append(token)
            def ltp(self, segment, sid):
                raise server.DhanRateLimitError("Dhan rate limit reached")
        with patch.dict("os.environ", {"DHAN_CLIENT_ID": "test-client"}), \
             patch.object(server, "DhanFeed", FakeDhan), \
             patch.object(Path, "read_text", return_value="provisioned-test"):
            app = server.create_app(pairing_key=KEY)
            response = TestClient(app).post("/dhan/ltp", json={"symbol": "NIFTY"},
                                            headers={"X-BotKing-Key": KEY})
        self.assertEqual(response.status_code, 429)
        self.assertEqual(len(seen), 1)


if __name__ == "__main__":
    unittest.main()
