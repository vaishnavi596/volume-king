"""Offline Oracle ↔ Android Dhan read-only transport compatibility checks.

These verify SOURCE contract wiring only.  Never perform network I/O.
They must not claim the customized Oracle production service is deployed.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SERVER = (ROOT / "backend" / "server.py").read_text(encoding="utf-8")
CLIENT = (ROOT / "src" / "server_feed.py").read_text(encoding="utf-8")
MAIN = (ROOT / "src" / "main.py").read_text(encoding="utf-8")

# Explicit app→Oracle dependencies, with methods matched against source.
APP_ROUTES = {
    "/v2/snapshot": "GET",
    "/dhan/ltp-batch": "POST",
    "/dhan/index-ltp-batch": "POST",
    "/dhan/selected-ltp-batch": "POST",
    "/dhan/intraday": "POST",
    "/dhan/option-expiries": "POST",
    "/dhan/option-chain": "POST",
}


class AppOracleRouteParity(unittest.TestCase):
    def test_all_core_routes_have_matching_server_methods(self):
        for path, method in APP_ROUTES.items():
            with self.subTest(path=path):
                self.assertIn(f'@app.{method.lower()}("{path}")', SERVER)
                self.assertIn(f'"{path}"', CLIENT)

    def test_client_get_and_post_use_same_pairing_header_as_server(self):
        self.assertIn('"X-BotKing-Key": checked_pairing_key(self._pairing_key)', CLIENT)
        self.assertIn('x_botking_key: Optional[str] = Header(default=None)', SERVER)
        self.assertIn('method="GET"', CLIENT)
        self.assertIn('method="POST"', CLIENT)

    def test_server_owned_equity_cache_is_opt_in_not_automatically_fresh(self):
        self.assertIn('BOTKING_226_INGEST_ENABLED', SERVER)
        self.assertIn('get("BOTKING_226_INGEST_ENABLED", "0")', SERVER)
        self.assertIn('max(60, min(900,', SERVER)
        self.assertIn('recently_collected', SERVER)
        self.assertIn('result.get("collection_status") != "recently_collected"', CLIENT)
        self.assertIn('age > 120', CLIENT)
        # Every release must acknowledge that a disabled collector is not
        # made active by just changing the Android polling interval.

    def test_quotes_and_history_remain_read_only_and_historical(self):
        self.assertIn('live_orders_enabled', SERVER)
        self.assertIn('result.get("live_orders_enabled") is not False', CLIENT)
        self.assertIn('def equity_quotes_with_bootstrap(self):', CLIENT)
        self.assertIn('self._call("/dhan/ltp-batch", {})', CLIENT)
        self.assertIn('historical_unverified', SERVER)
        self.assertIn('async def super_five_minute_refresh():', MAIN)

    def test_server_readiness_is_authenticated_sanitized_and_orders_off(self):
        self.assertIn('@app.get("/v2/server-readiness")', SERVER)
        self.assertIn('def botking_server_readiness(', SERVER)
        self.assertIn('def server_readiness(self):', CLIENT)
        start = SERVER.index('def botking_server_readiness(')
        end = SERVER.index('    @app.get("/v2/snapshot")', start)
        body = SERVER[start:end]
        self.assertIn('hmac.compare_digest', body)
        self.assertIn('"configured_enabled": enabled', body)
        self.assertIn('"interval_seconds": snapshot_collection_interval', body)
        self.assertIn('"last_success_age_seconds"', body)
        self.assertIn('"broker_submission_allowed": False', body)
        self.assertIn('"live_orders_enabled": False', body)
        self.assertNotIn('access_token', body)
        self.assertNotIn('dhan_market_token()', body)

    def test_assessment_is_protected_and_all_factors_fail_closed(self):
        self.assertIn('@app.get("/v2/assessment/{symbol}")', SERVER)
        self.assertIn('def assessment(self, symbol):', CLIENT)
        a = SERVER.index("def botking_read_only_assessment(")
        b = SERVER.index('    @app.get("/v2/server-readiness")', a)
        section = SERVER[a:b]
        self.assertIn('hmac.compare_digest', section)
        self.assertIn('HTTPException(403', section)
        self.assertIn('HTTPException(422', section)
        self.assertIn('("oi_support", "oi_resistance", "max_pain", "pcr", "candle_trend")', section)
        self.assertIn('("news", "futures", "options", "candle")', section)
        self.assertIn('"bullish_score": None', section)
        self.assertIn('"bearish_score": None', section)
        self.assertIn('"signal_eligible": False', section)
        self.assertIn('"live_orders_enabled": False', section)
        self.assertNotIn('DhanFeed(', section)
        self.assertNotIn('dhan_market_token()', section)

    def test_no_new_unverified_four_lane_api_paths_were_assumed(self):
        # Future server coordinator routes need paired client+server+tests.
        self.assertNotIn('"/v3/pipeline/', CLIENT)
        self.assertNotIn('@app.get("/v3/pipeline/', SERVER)

if __name__ == "__main__":
    unittest.main()
