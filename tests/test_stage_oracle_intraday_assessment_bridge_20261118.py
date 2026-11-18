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

    def test_publish_failure_preserves_return_and_does_not_retry_dhan(self):
        # An informational Assessment failure must not break a successful candle read.
        source = FAKE.replace(
            'published.append((account, symbol, kind, timeframe))',
            'raise RuntimeError("assessment cache unavailable")',
        )
        configure_fake(source)
        namespace = {}
        exec(compile(stage.stage_source(source), "<synthetic-bridge>", "exec"),
             namespace)
        route, published = namespace["create_app"]()
        for mode in range(4):
            data = route(mode)
            self.assertEqual(set(data), set(stage.EXPECTED_KEYS))
            self.assertFalse(data["live_orders_enabled"])
        self.assertEqual(published, [])

    def test_source_and_freshness_must_match_exactly(self):
        # Historical/cached evidence is never promoted from arbitrary providers.
        source = FAKE.replace(
            'if body == 1:\\n            return',
            'if body == 1:\\n            return',
        ).replace(
            '"symbol":"HDFCBANK","source":"dhan"',
            '"symbol":"HDFCBANK","source":"yahoo"',
        ).replace(
            '"symbol":"NIFTY","source":"dhan","interval":"5m","bars":[[1,2],[2,3]],"freshness":"historical_unverified"',
            '"symbol":"NIFTY","source":"dhan","interval":"5m","bars":[[1,2],[2,3]],"freshness":"live_verified"',
        )
        configure_fake(source)
        namespace = {}
        exec(compile(stage.stage_source(source), "<synthetic-bridge>", "exec"),
             namespace)
        route, published = namespace["create_app"]()
        for mode in range(4):
            route(mode)
        self.assertEqual(published, [
            ("test-account", "NIFTY", "candle", "1m")
        ])

    def test_route_local_import_not_available_to_intraday_helper(self):
        # Mimic the live Oracle route: canonical publisher imports its own
        # dependencies; that import does not bind them in dhan_intraday.
        scoped = FAKE.replace(
            '    def cached_candles(symbol, interval, key):\n',
            '    def cached_candles(symbol, interval, key):\n'
            '        from assessment_state import publish\n'
            '        from assessment_scope import current_scope\n',
        )
        self.assertNotEqual(scoped, FAKE)
        configure_fake(scoped)
        with self.assertRaisesRegex(
            ValueError, "INTRADAY_PUBLISH_BINDINGS_UNAVAILABLE"
        ):
            stage.stage_source(scoped)

    def test_real_five_field_canonical_payload_blocks_unsafe_stage(self):
        canonical = FAKE.replace(
            '{"bars": []}, timeframe=interval)',
            '{"bars": [], "observed_at": None, "interval": interval, '
            '"freshness": "historical_unverified", "signal_eligible": False}, '
            'timeframe=interval)',
        )
        self.assertNotEqual(canonical, FAKE)
        configure_fake(canonical)
        with self.assertRaisesRegex(
            ValueError, "CANONICAL_PAYLOAD_PARITY_UNIMPLEMENTED"
        ):
            stage.stage_source(canonical)

    def test_dynamic_canonical_payload_is_not_assumed_compatible(self):
        canonical = FAKE.replace(
            '{"bars": []}, timeframe=interval)',
            'dict(bars=[]), timeframe=interval)',
        )
        self.assertNotEqual(canonical, FAKE)
        configure_fake(canonical)
        with self.assertRaisesRegex(
            ValueError, "CANONICAL_PAYLOAD_SHAPE_UNSUPPORTED"
        ):
            stage.stage_source(canonical)

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
