"""Offline tests for the SHA-locked, non-deploying Oracle Assessment bridge stager."""
import ast
import hashlib
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "stage_oracle_intraday_assessment_bridge_20261118.py"
spec = importlib.util.spec_from_file_location("bk_intraday_bridge_stage", SCRIPT)
stage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage)

FAKE = '''
def create_app():
    published = []
    def scope():
        return "test-account"
    def publish(account, symbol, kind, value, timeframe=None):
        published.append((account, symbol, kind, timeframe))
    def _assessment_bars_completed(rows, minutes):
        return (len(rows) == 2 and rows[-1][0] > rows[-2][0]
                and minutes in (1, 3, 5))
    def cached_candles(symbol, interval, key):
        publish(scope(), symbol, "candle", {"bars": []}, timeframe=interval)
    def dhan_intraday(body, key=None):
        if body == 0:
            return {"symbol":"NIFTY","source":"dhan","interval":"1m","bars":[[1,2],[2,3]],"freshness":"historical_unverified","live_orders_enabled":False}
        if body == 1:
            return {"symbol":"HDFCBANK","source":"dhan","interval":"3m","bars":[[1,2],[2,3]],"freshness":"historical_unverified","live_orders_enabled":False}
        if body == 2:
            return {"symbol":"NIFTY","source":"dhan","interval":"5m","bars":[],"freshness":"stale_or_missing","live_orders_enabled":False}
        return {"symbol":"NIFTY","source":"dhan","interval":"5m","bars":[[1,2],[2,3]],"freshness":"historical_unverified","live_orders_enabled":False}
    return dhan_intraday, published
'''


def configure_fake(source):
    stage.EXPECTED_SHA = hashlib.sha256(source.encode()).hexdigest()
    route = stage.named_function(ast.parse(source), "dhan_intraday")
    stage.EXPECTED_RETURNS = tuple(n.lineno for n in stage.response_returns(route))


class OracleIntradayStageRegression(unittest.TestCase):
    def setUp(self):
        self.old_sha = stage.EXPECTED_SHA
        self.old_lines = stage.EXPECTED_RETURNS

    def tearDown(self):
        stage.EXPECTED_SHA = self.old_sha
        stage.EXPECTED_RETURNS = self.old_lines

    def test_four_returns_keep_contract_and_only_good_bars_publish(self):
        configure_fake(FAKE)
        patched = stage.stage_source(FAKE)
        ast.parse(patched)
        module = {}
        exec(compile(patched, "<synthetic-bridge>", "exec"), module)
        handler, published = module["create_app"]()
        for choice in range(4):
            response = handler(choice)
            self.assertEqual(set(response), set(stage.EXPECTED_KEYS))
            self.assertFalse(response["live_orders_enabled"])
        self.assertEqual(published, [
            ("test-account", "NIFTY", "candle", "1m"),
            ("test-account", "HDFCBANK", "candle", "3m"),
            ("test-account", "NIFTY", "candle", "5m"),
        ])
        self.assertNotIn("/dhan/", patched)
        self.assertIn("_assessment_bars_completed", patched)

    def test_sha_mismatch_fails_closed(self):
        configure_fake(FAKE)
        with self.assertRaisesRegex(ValueError, "SOURCE_SHA_MISMATCH"):
            stage.stage_source(FAKE + "\n# changed source\n")

    def test_local_scope_not_copied_without_mapping(self):
        unsafe = FAKE.replace(
            'publish(scope(), symbol, "candle", {"bars": []}, timeframe=interval)',
            'local_scope = "unsafe"\n        publish(local_scope, symbol, "candle", {"bars": []}, timeframe=interval)',
        )
        configure_fake(unsafe)
        with self.assertRaisesRegex(ValueError, "PUBLISH_SCOPE_NEEDS_EXPLICIT_MAPPING"):
            stage.stage_source(unsafe)

    def test_schema_drift_blocked_even_with_updated_sha(self):
        changed = FAKE.replace('"live_orders_enabled":False', '"different":False', 1)
        configure_fake(changed)
        with self.assertRaisesRegex(ValueError, "RETURN_SCHEMA_CHANGED"):
            stage.stage_source(changed)


if __name__ == "__main__":
    unittest.main()
