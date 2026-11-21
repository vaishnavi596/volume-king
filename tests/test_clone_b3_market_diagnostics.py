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

    def test_missing_sensex_segment_redacted_partial_response(self):
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
        self.assertEqual(entries, [("quotes", "SENSEX", "mapping", "missing_segment")])
        self.assertNotIn(self.KEY.decode(), repr(entries))

    def test_invalid_sensex_price_no_false_quote(self):
        class Provider:
            def batch_ltp(self, instruments):
                return {"status": "success", "data": {
                    "IDX_I": {"13": {"last_price": 25000.0}},
                    "BSE_I": {"51": {"last_price": 0}}}}
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

    def test_paced_index_retry_has_sanitized_429_category(self):
        class Provider:
            def batch_ltp(self, instruments):
                return {"status": "success", "data": {
                    "IDX_I": {"13": {"last_price": 25000.0}},
                    "BSE_I": {"51": {"last_price": 70000.0}}}}
        http = self.client(Provider())
        first = http.post("/clone-v2/market/quotes", headers=self.headers(),
                          json={"symbols": ["NIFTY"]})
        self.assertEqual(first.status_code, 200)
        with patch("backend.clone_v2_gateway.DIAGNOSTIC_LOGGER.warning") as log:
            second = http.post("/clone-v2/market/quotes", headers=self.headers(),
                               json={"symbols": ["SENSEX"]})
        self.assertEqual(second.status_code, 429)
        self.assertEqual([call.args[1:] for call in log.call_args_list],
                         [("quotes", "SENSEX", "cooldown", "rate_limited")])

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
