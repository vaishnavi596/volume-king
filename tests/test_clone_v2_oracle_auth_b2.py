"""B2 isolated Oracle clone login contract: all checks offline, no broker calls."""
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.clone_v2_gateway import create_app, private_ssk


class CloneOracleAuthTests(unittest.TestCase):
    def setUp(self):
        self.key = b"k" * 40
        self.http = TestClient(create_app(key_bytes=self.key))

    def test_finnifty_option_only_underlying_mapping(self):
        class Provider:
            def option_expiries(self, segment, sid):
                self.expiry_args = (segment, sid)
                return ["2099-12-31"]
            def option_chain(self, segment, sid, expiry):
                self.chain_args = (segment, sid, expiry)
                return {"status": "success", "data": {"last_price": 25000.0, "oc": {
                    "24950.0": {"ce": {"oi": 100}, "pe": {"oi": 120}},
                    "25000.0": {"ce": {"oi": 150}, "pe": {"oi": 90}}
                }}}
        feed = Provider()
        http = TestClient(create_app(key_bytes=self.key,market_feed_factory=lambda:feed,
                                     market_registry={"RELIANCE":("NSE_EQ",2885)}))
        headers={"X-BotKing-Key": self.key.decode()}
        res=http.post("/clone-v2/market/options/expiries",
                      headers=headers,json={"symbol":"FINNIFTY"})
        self.assertEqual(res.status_code,200,res.text)
        self.assertEqual(feed.expiry_args,("IDX_I",27))
        self.assertEqual(res.json()["expiries"],["2099-12-31"])
        # Option-only mapping must not silently add a fourth dashboard quote slot.
        self.assertEqual(http.post("/clone-v2/market/quotes",headers=headers,
                                   json={"symbols":["FINNIFTY"]}).status_code,422)

    def test_no_key_fails_closed(self):
        res = self.http.get("/clone-v2/status")
        self.assertEqual(res.status_code, 403)

    def test_wrong_key_fails_closed(self):
        res = self.http.get("/clone-v2/status", headers={"X-BotKing-Key": "q" * 40})
        self.assertEqual(res.status_code, 403)

    def test_approved_key_exact_contract(self):
        res = self.http.get("/clone-v2/status", headers={"X-BotKing-Key": self.key.decode()})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["cache-control"], "no-store")
        self.assertEqual(res.json(), {
            "protocol": "botking-clone-v2",
            "authenticated": True,
            "read_only": True,
            "live_orders_enabled": False,
            "pipeline": "dhan-oracle-clone",
            "status": "ready",
        })

    def test_no_legacy_v1_or_pilot_v2_routes(self):
        for uri in ("/dhan/status", "/v2-pilot/auth/challenge", "/clone-v2/quotes",
                    "/clone-v2/orders"):
            self.assertEqual(self.http.get(uri).status_code, 404)

    def test_health_not_market_data_proof(self):
        res = self.http.get("/clone-v2/health")
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.json()["live_data_verified"])

    def test_key_provisioning_not_auto_bootstrapped(self):
        with patch.dict(os.environ, {"BOTKING_CLONE_V2_SSK_FILE": ""}):
            with self.assertRaises(ValueError):
                create_app()

    def test_insecure_private_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "key"
            path.write_bytes(self.key)
            path.chmod(0o644)
            with self.assertRaises(ValueError):
                private_ssk(str(path))


    def test_clone_b3_market_quotes_symmetric_request_response(self):
        seen = []
        class FakeProvider:
            def batch_ltp(self, instruments):
                seen.append(instruments)
                return {"status": "success", "data": {
                    "NSE_EQ": {"2885": {"last_price": 1440.5}},
                    "IDX_I": {"13": {"last_price": 25950.25}}}}
        app = create_app(key_bytes=self.key, market_feed_factory=FakeProvider,
                         market_registry={"RELIANCE": ("NSE_EQ", 2885)})
        http = TestClient(app)
        url = "/clone-v2/market/quotes"
        payload = {"symbols": ["RELIANCE", "NIFTY"]}
        self.assertEqual(http.post(url, json=payload).status_code, 403)
        self.assertEqual(http.post(url, headers={"X-BotKing-Key": "z" * 40},
                                   json=payload).status_code, 403)
        good = http.post(url, headers={"X-BotKing-Key": self.key.decode()}, json=payload)
        self.assertEqual(good.status_code, 200)
        self.assertEqual(good.headers["cache-control"], "no-store")
        body = good.json()
        self.assertEqual(body["quotes"]["RELIANCE"]["ltp"], 1440.5)
        self.assertEqual(body["quotes"]["NIFTY"]["ltp"], 25950.25)
        self.assertIs(body["live_orders_enabled"], False)
        self.assertEqual(body["freshness"], "unverified")
        self.assertEqual(len(seen), 1)
        again = http.post(url, headers={"X-BotKing-Key": self.key.decode()}, json=payload)
        self.assertEqual(again.status_code, 200)
        self.assertEqual(len(seen), 1, "same app request must share cache")

    def test_clone_b3_rejects_duplicate_unknown_and_unbounded_requests(self):
        http = TestClient(create_app(key_bytes=self.key, market_registry={"RELIANCE": ("NSE_EQ", 2885)},
                                     market_feed_factory=lambda: None))
        key = {"X-BotKing-Key": self.key.decode()}
        for symbols in ([], ["RELIANCE", "RELIANCE"], ["UNKNOWN"], ["NIFTY"] * 74,
                        ["RELIANCE", {"unhashable": True}]):
            with self.subTest(symbols=symbols):
                res = http.post("/clone-v2/market/quotes", headers=key, json={"symbols": symbols})
                self.assertEqual(res.status_code, 422)
        self.assertEqual(http.post("/clone-v2/orders", headers=key, json={}).status_code, 404)


    def test_clone_b3_registry_candles_and_options_are_ssk_protected(self):
        from datetime import datetime, timedelta, timezone
        # Dhan-listed expiries are validated using India exchange calendar day.
        # GitHub's UTC date can be yesterday during 00:00–05:29 IST.
        today = datetime.now(timezone(timedelta(hours=5, minutes=30))).date().isoformat()
        class FakeProvider:
            def intraday(self, args):
                self.assert_args = args
                return {"status": "success", "timestamp": [1770000000, 1770000060],
                        "open": [100, 101], "high": [102, 103],
                        "low": [99, 100], "close": [101, 102],
                        "volume": [1000, 1100]}
            def option_expiries(self, segment, sid):
                return [today]
            def option_chain(self, segment, sid, expiry):
                rows = {}
                for n in range(90, 120, 5):
                    rows[str(n)] = {"ce": {"oi": 1000, "volume": 100},
                                    "pe": {"oi": 1000, "volume": 100}}
                return {"status": "success", "data": {"last_price": 102.0,
                        "oc": rows}}
        http = TestClient(create_app(key_bytes=self.key,
                   market_feed_factory=FakeProvider,
                   market_registry={"RELIANCE": ("NSE_EQ", 2885)}))
        key = {"X-BotKing-Key": self.key.decode()}
        candle = {"symbol": "RELIANCE", "interval": 1,
                  "from_date": today, "to_date": today}
        path = "/clone-v2/market/candles"
        self.assertEqual(http.post(path, json=candle).status_code, 403)
        response = http.post(path, headers=key, json=candle)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["bars"]), 2)
        self.assertEqual(response.json()["freshness"], "historical_unverified")
        self.assertIs(response.json()["live_orders_enabled"], False)
        self.assertEqual(http.post(path, headers=key, json={**candle, "interval": 2}).status_code, 422)

        path = "/clone-v2/market/verify"
        self.assertEqual(http.post(path, headers=key, json={"symbol": "RELIANCE"}).status_code, 200)
        self.assertEqual(http.post(path, headers=key, json={"symbol": "UNKNOWN"}).status_code, 422)

        expiry_path = "/clone-v2/market/options/expiries"
        self.assertEqual(http.post(expiry_path, json={"symbol": "NIFTY"}).status_code, 403)
        expiries = http.post(expiry_path, headers=key, json={"symbol": "NIFTY"})
        self.assertEqual(expiries.status_code, 200)
        self.assertEqual(expiries.json()["expiries"], [today])
        chain_path = "/clone-v2/market/options/chain"
        chain = http.post(chain_path, headers=key, json={"symbol": "NIFTY", "expiry": today})
        self.assertEqual(chain.status_code, 200)
        self.assertIs(chain.json()["signal_eligible"], False)
        self.assertIs(chain.json()["live_orders_enabled"], False)
        self.assertEqual(http.post("/clone-v2/orders", headers=key, json={}).status_code, 404)


if __name__ == "__main__":
    unittest.main()
