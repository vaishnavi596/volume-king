"""Two phones share one Oracle 51-equity bootstrap call, no Dhan network."""
import os
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from fastapi.testclient import TestClient
from backend.server import create_app


class TwoPhoneFixedEquityBootstrapTests(unittest.TestCase):
    def test_concurrent_identical_fixed_equity_batch_calls_provider_once(self):
        key = "K" * 48
        lock = threading.Lock()
        calls = [0]

        def fake_post(_self, endpoint, payload):
            self.assertEqual(endpoint, "/marketfeed/ltp")
            self.assertIn("NSE_EQ", payload)
            with lock:
                calls[0] += 1
            return {"status": "success",
                    "data": {"NSE_EQ": {"2885": {"last_price": 123.5}}}}

        with patch.dict(os.environ, {
            "DHAN_CLIENT_ID": "test-client",
            "BOTKING_226_INGEST_ENABLED": "0",
        }), patch("pathlib.Path.read_text", return_value="fake-read-only-token"), \
             patch("backend.server.DhanFeed._post", new=fake_post):
            app = create_app(pairing_key=key)
            with TestClient(app) as client:
                def phone():
                    return client.post("/dhan/ltp-batch", headers={"X-BotKing-Key": key})
                with ThreadPoolExecutor(max_workers=2) as pool:
                    results = list(pool.map(lambda _: phone(), range(2)))
            self.assertEqual([r.status_code for r in results], [200, 200])
            self.assertEqual(calls[0], 1)
            self.assertTrue(all(r.json()["quotes"]["RELIANCE"] == 123.5
                                for r in results))
            self.assertTrue(all(r.json()["live_orders_enabled"] is False
                                for r in results))

    def test_invalid_access_key_does_not_reuse_snapshot(self):
        key = "K" * 48
        with patch.dict(os.environ, {
            "DHAN_CLIENT_ID": "test-client",
            "BOTKING_226_INGEST_ENABLED": "0",
        }), patch("pathlib.Path.read_text", return_value="fake-read-only-token"):
            app = create_app(pairing_key=key)
            with TestClient(app) as client:
                response = client.post("/dhan/ltp-batch",
                                       headers={"X-BotKing-Key": "bad"})
            self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
