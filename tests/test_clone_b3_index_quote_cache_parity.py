"""V1-parity index quote TTL: offline mock requests only, no Oracle/Dhan access."""
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from backend.clone_v2_gateway import create_app


class CloneIndexBatchCacheParityTests(unittest.TestCase):
    KEY = b"k" * 40
    URL = "/clone-v2/market/quotes"

    def make_client(self, omit_sensex=False):
        class FakeDhan:
            def __init__(self):
                self.calls = 0
            def batch_ltp(self, instruments):
                self.calls += 1
                data = {"IDX_I": {"13": {"last_price": 25000.0},
                                  "25": {"last_price": 60000.0}},
                        "NSE_EQ": {"2885": {"last_price": 1500.0}}}
                if not omit_sensex:
                    data["IDX_I"]["51"] = {"last_price": 80000.0}
                return {"status": "success", "data": data}
        feed = FakeDhan()
        client = TestClient(create_app(
            key_bytes=self.KEY, market_feed_factory=lambda: feed,
            market_registry={"RELIANCE": ("NSE_EQ", 2885)}))
        return feed, client

    def quote(self, client, symbols):
        return client.post(self.URL, headers={"X-BotKing-Key": self.KEY.decode()},
                           json={"symbols": symbols})

    def test_complete_three_index_batch_reused_for_60_seconds(self):
        feed, client = self.make_client()
        with patch("backend.clone_v2_gateway.time") as fake_time:
            fake_time.monotonic.return_value = 100.0
            first = self.quote(client, ["NIFTY", "BANKNIFTY", "SENSEX"])
            fake_time.monotonic.return_value = 145.0
            second = self.quote(client, ["SENSEX", "BANKNIFTY", "NIFTY"])
            self.assertEqual(first.status_code, 200)
            self.assertEqual(second.status_code, 200)
            self.assertEqual(feed.calls, 1)
            self.assertEqual(second.json()["unavailable"], [])
            fake_time.monotonic.return_value = 161.0
            third = self.quote(client, ["NIFTY", "BANKNIFTY", "SENSEX"])
        self.assertEqual(third.status_code, 200)
        self.assertEqual(feed.calls, 2)

    def test_partial_sensex_remains_20_second_recovery(self):
        feed, client = self.make_client(omit_sensex=True)
        with patch("backend.clone_v2_gateway.time") as fake_time, patch(
                "backend.clone_v2_gateway.DIAGNOSTIC_LOGGER.warning"):
            fake_time.monotonic.return_value = 100.0
            first = self.quote(client, ["NIFTY", "BANKNIFTY", "SENSEX"])
            fake_time.monotonic.return_value = 115.0
            second = self.quote(client, ["NIFTY", "BANKNIFTY", "SENSEX"])
            fake_time.monotonic.return_value = 125.0
            third = self.quote(client, ["NIFTY", "BANKNIFTY", "SENSEX"])
        self.assertTrue(all(x.status_code == 200 for x in (first, second, third)))
        self.assertEqual(first.json()["unavailable"], ["SENSEX"])
        self.assertEqual(feed.calls, 2)

    def test_equity_selections_keep_20_second_ttl(self):
        feed, client = self.make_client()
        with patch("backend.clone_v2_gateway.time") as fake_time:
            fake_time.monotonic.return_value = 100.0
            first = self.quote(client, ["RELIANCE"])
            fake_time.monotonic.return_value = 115.0
            second = self.quote(client, ["RELIANCE"])
            fake_time.monotonic.return_value = 125.0
            third = self.quote(client, ["RELIANCE"])
        self.assertTrue(all(x.status_code == 200 for x in (first, second, third)))
        self.assertEqual(feed.calls, 2)


if __name__ == "__main__":
    unittest.main()
