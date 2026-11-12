import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend import server


class DhanBatchTests(unittest.TestCase):
    def test_verified_mapping_has_51_equities(self):
        equities = {name: sid for name, (segment, sid, _) in server.DHAN_VERIFIED_INSTRUMENTS.items() if segment == "NSE_EQ"}
        self.assertEqual(len(equities), 51)
        self.assertEqual(equities["TMPV"], 3456)
        self.assertEqual(equities["TMCV"], 759782)
        self.assertEqual(server.DHAN_VERIFIED_INSTRUMENTS["NIFTY"][:2], ("IDX_I", 13))

    def test_empty_successful_upstream_is_reported_as_failure(self):
        """HTTP 200 from Dhan is not evidence that live quotes were delivered."""
        from pathlib import Path
        fake = {"status": "success", "data": {"NSE_EQ": {}}}
        with patch.dict("os.environ", {"BOTKING_PAIRING_KEY": "test-pairing-key-with-at-least-32-characters", "DHAN_CLIENT_ID": "test-client"}), \
             patch.object(Path, "read_text", return_value="test-token"), \
             patch.object(server.DhanFeed, "_post", return_value=fake):
            app = server.create_app()
            response = TestClient(app).post("/dhan/ltp-batch", headers={"X-BotKing-Key": "test-pairing-key-with-at-least-32-characters"}, json={})
        self.assertEqual(response.status_code, 502)
        self.assertIn("no market data", response.json()["detail"])
        self.assertNotIn("test-token", response.text)

    def test_nonempty_upstream_with_all_invalid_prices_is_failure(self):
        """Dhan HTTP success must not publish an empty successful snapshot."""
        from pathlib import Path
        fake = {"status": "success", "data": {"NSE_EQ": {
            "2885": {"last_price": 0}, "1333": {"last_price": -1}}}}
        with patch.dict("os.environ", {"BOTKING_PAIRING_KEY": "test-pairing-key-with-at-least-32-characters", "DHAN_CLIENT_ID": "test-client"}), \
             patch.object(Path, "read_text", return_value="test-token"), \
             patch.object(server.DhanFeed, "_post", return_value=fake):
            app = server.create_app()
            client = TestClient(app)
            headers = {"X-BotKing-Key": "test-pairing-key-with-at-least-32-characters"}
            response = client.post("/dhan/ltp-batch", headers=headers, json={})
            snapshot = client.get("/v2/snapshot", headers=headers)
        self.assertEqual(response.status_code, 502)
        self.assertEqual(snapshot.status_code, 200)
        self.assertEqual(snapshot.json()["collection_status"], "not_collected")
        self.assertEqual(snapshot.json()["quotes"], {})

    def test_batch_endpoint_validates_quotes_and_does_not_trade(self):
        # The batch endpoint must not invent prices for absent instruments.
        from pathlib import Path
        fake = {"status": "success", "data": {"NSE_EQ": {
            "2885": {"last_price": 1320},
            "1333": {"last_price": 788.25},
        }}}
        with patch.dict("os.environ", {"BOTKING_PAIRING_KEY": "test-pairing-key-with-at-least-32-characters", "DHAN_CLIENT_ID": "test-client"}), \
             patch.object(Path, "read_text", return_value="test-token"), \
             patch.object(server.DhanFeed, "_post", return_value=fake):
            app = server.create_app()
            response = TestClient(app).post("/dhan/ltp-batch", headers={"X-BotKing-Key": "test-pairing-key-with-at-least-32-characters"}, json={})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["quotes"]["RELIANCE"], 1320)
        self.assertEqual(body["quotes"]["HDFCBANK"], 788.25)
        self.assertIn("TMCV", body["unavailable"])
        self.assertEqual(len(body["quotes"]) + len(body["unavailable"]), 51)
        self.assertIs(body["live_orders_enabled"], False)
        self.assertEqual(body["freshness"], "unverified")


if __name__ == "__main__":
    unittest.main()
