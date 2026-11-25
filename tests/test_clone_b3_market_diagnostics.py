"""Clone B3 redacted index diagnostics; mocked provider, no market network."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import unittest

from fastapi.testclient import TestClient
from backend.clone_v2_gateway import create_app


class CloneMarketDiagnosticsTests(unittest.TestCase):
    KEY = b"k" * 40

    def client(self, provider):
        app = create_app(key_bytes=self.KEY,
                         market_feed_factory=lambda: provider,
                         market_registry={"RELIANCE": ("NSE_EQ", 2885)})
        return TestClient(app)

    def headers(self):
        return {"X-BotKing-Key": self.KEY.decode()}

    def test_missing_sensex_security_id_redacted_partial_response(self):
        class Provider:
            def batch_ltp(self, instruments):
                return {"status": "success", "data": {
                    "IDX_I": {"13": {"last_price": 25000.0},
                              "25": {"last_price": 60000.0}}}}
        with patch("backend.clone_v2_gateway.DIAGNOSTIC_LOGGER.warning") as log:
            res = self.client(Provider()).post(
                "/clone-v2/market/quotes", headers=self.headers(),
                json={"symbols": ["NIFTY", "BANKNIFTY", "SENSEX"]})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["unavailable"], ["SENSEX"])
        entries = [call.args[1:] for call in log.call_args_list]
        self.assertEqual(entries, [("quotes", "SENSEX", "mapping", "missing_security_id")])
        self.assertNotIn(self.KEY.decode(), repr(entries))

    def test_invalid_sensex_price_no_false_quote(self):
        class Provider:
            def batch_ltp(self, instruments):
                return {"status": "success", "data": {
                    "IDX_I": {"13": {"last_price": 25000.0},
                              "51": {"last_price": 0}}}}
        with patch("backend.clone_v2_gateway.DIAGNOSTIC_LOGGER.warning") as log:
            res = self.client(Provider()).post(
                "/clone-v2/market/quotes", headers=self.headers(),
                json={"symbols": ["NIFTY", "SENSEX"]})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["unavailable"], ["SENSEX"])
        self.assertIn(("quotes", "SENSEX", "validation", "invalid_price"),
                      [call.args[1:] for call in log.call_args_list])

    def test_invalid_sensex_candles_logged_without_payload(self):
        class Provider:
            def intraday(self, args):
                return {"status": "success", "timestamp": [1800000000],
                        "open": [100], "high": [99], "low": [98],
                        "close": [101], "volume": [100]}
        today = datetime.now(timezone(timedelta(hours=5, minutes=30))).date().isoformat()
        with patch("backend.clone_v2_gateway.DIAGNOSTIC_LOGGER.warning") as log:
            res = self.client(Provider()).post(
                "/clone-v2/market/candles", headers=self.headers(),
                json={"symbol": "SENSEX", "interval": 1,
                      "from_date": today, "to_date": today})
        self.assertEqual(res.status_code, 502)
        self.assertEqual([call.args[1:] for call in log.call_args_list],
                         [("candles", "SENSEX", "validation", "invalid_bars")])

    def test_mapped_equity_candle_failure_is_logged_without_provider_payload(self):
        class Provider:
            def intraday(self, args):
                return {"status": "success", "timestamp": [1800000000],
                        "open": [100], "high": [99], "low": [98],
                        "close": [101], "volume": [100]}
        today = datetime.now(timezone(timedelta(hours=5, minutes=30))).date().isoformat()
        with patch("backend.clone_v2_gateway.DIAGNOSTIC_LOGGER.warning") as log:
            res = self.client(Provider()).post(
                "/clone-v2/market/candles", headers=self.headers(),
                json={"symbol": "RELIANCE", "interval": 5,
                      "from_date": today, "to_date": today})
        self.assertEqual(res.status_code, 502)
        self.assertEqual([call.args[1:] for call in log.call_args_list],
                         [("candles", "RELIANCE", "validation", "invalid_bars")])
        self.assertNotIn(self.KEY.decode(), repr(log.call_args_list))


    def test_paced_index_retry_queues_instead_of_gateway_429(self):
        import time
        calls=[]
        class Provider:
            def batch_ltp(self, instruments):
                calls.append(time.monotonic())
                return {"status": "success", "data": {
                    "IDX_I": {"13": {"last_price": 25000.0},
                              "51": {"last_price": 70000.0}}}}
        http = self.client(Provider())
        first = http.post("/clone-v2/market/quotes", headers=self.headers(),
                          json={"symbols": ["NIFTY"]})
        self.assertEqual(first.status_code, 200)
        with patch("backend.clone_v2_gateway.DIAGNOSTIC_LOGGER.warning") as log:
            second = http.post("/clone-v2/market/quotes", headers=self.headers(),
                               json={"symbols": ["SENSEX"]})
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()["quotes"]["SENSEX"]["ltp"], 70000.0)
        self.assertEqual(len(calls), 2)
        self.assertGreaterEqual(calls[1]-calls[0], 1.04)
        log.assert_not_called()

    def test_provider_quota_429_is_not_gateway_pacing(self):
        from backend.dhan_feed import DhanRateLimitError
        class Provider:
            def batch_ltp(self, instruments):
                raise DhanRateLimitError("sanitized rate limit")
        with patch("backend.clone_v2_gateway.DIAGNOSTIC_LOGGER.warning"):
            res = self.client(Provider()).post(
                "/clone-v2/market/quotes", headers=self.headers(),
                json={"symbols": ["NIFTY"]})
        self.assertEqual(res.status_code, 429)
        self.assertEqual(res.headers["X-BotKing-429-Stage"], "PROVIDER_QUOTA")
        self.assertEqual(res.headers["Retry-After"], "30")

    def test_empty_dhan_segments_are_paced_and_never_marked_live(self):
        class Provider:
            calls = 0
            def batch_ltp(self, instruments):
                self.calls += 1
                return {"status": "success", "data": {"IDX_I": {}, "NSE_EQ": {}}}
        provider = Provider()
        http = self.client(provider)
        with patch("backend.clone_v2_gateway.DIAGNOSTIC_LOGGER.warning"):
            first = http.post("/clone-v2/market/quotes", headers=self.headers(),
                              json={"symbols": ["NIFTY", "RELIANCE"]})
            second = http.post("/clone-v2/market/quotes", headers=self.headers(),
                               json={"symbols": ["NIFTY", "RELIANCE"]})
        self.assertEqual(first.status_code, 502)
        self.assertEqual(first.headers.get("X-BotKing-Quote-Failure-Stage"), "RESPONSE")
        self.assertEqual(first.headers.get("X-BotKing-Quote-Response-State"), "EMPTY_SEGMENTS")
        self.assertEqual(first.headers.get("Retry-After"), "30")
        self.assertEqual(second.status_code, 429)
        self.assertEqual(second.headers.get("X-BotKing-429-Stage"), "PROVIDER_COOLDOWN")
        self.assertEqual(provider.calls, 1)
        self.assertNotIn("quotes", first.json())
        self.assertNotIn("quotes", second.json())

    def test_candle_quota_blocks_other_uncached_routes(self):
        from backend.dhan_feed import DhanRateLimitError
        class Provider:
            calls = 0
            def intraday(self, args):
                self.calls += 1
                raise DhanRateLimitError("sanitized")
            def batch_ltp(self, instruments):
                raise AssertionError("quota bypass")
            def option_expiries(self, *args):
                raise AssertionError("quota bypass")
        p = Provider()
        http = self.client(p)
        today = datetime.now(timezone(timedelta(hours=5, minutes=30))).date().isoformat()
        request = {"symbol":"NIFTY","interval":1,"from_date":today,"to_date":today}
        first = http.post("/clone-v2/market/candles", headers=self.headers(), json=request)
        self.assertEqual(first.status_code, 429)
        self.assertEqual(first.headers["X-BotKing-429-Stage"], "PROVIDER_QUOTA")
        for path, body in (("candles",request),("quotes",{"symbols":["NIFTY"]}),
                           ("options/expiries",{"symbol":"NIFTY"})):
            res = http.post("/clone-v2/market/"+path, headers=self.headers(), json=body)
            self.assertEqual(res.status_code,429)
            self.assertEqual(res.headers["X-BotKing-429-Stage"],"PROVIDER_COOLDOWN")
            self.assertTrue(1 <= int(res.headers["Retry-After"]) <= 30)
        self.assertEqual(p.calls,1)

    def test_option_local_pacing_does_not_block_quote_lane(self):
        from backend.dhan_feed import DhanLocalPacingError
        class Provider:
            def option_expiries(self,*args):
                raise DhanLocalPacingError(2)
            def batch_ltp(self,instruments):
                return {"status":"success","data":{"IDX_I":{"13":{"last_price":25000}}}}
        http=self.client(Provider())
        res=http.post("/clone-v2/market/options/expiries",headers=self.headers(),json={"symbol":"NIFTY"})
        self.assertEqual(res.status_code,429)
        self.assertEqual(res.headers["X-BotKing-429-Stage"],"LOCAL_PACING")
        self.assertEqual(res.headers["Retry-After"],"2")
        self.assertEqual(http.post("/clone-v2/market/quotes",headers=self.headers(),
            json={"symbols":["NIFTY"]}).status_code,200)

    def test_unauthorized_call_never_logs_symbol(self):
        class Provider:
            def batch_ltp(self, instruments):
                raise AssertionError("unauthed provider invoked")
        with patch("backend.clone_v2_gateway.DIAGNOSTIC_LOGGER.warning") as log:
            res = self.client(Provider()).post(
                "/clone-v2/market/quotes",
                json={"symbols": ["SENSEX"]})
        self.assertEqual(res.status_code, 403)
        log.assert_not_called()


if __name__ == "__main__":
    unittest.main()
