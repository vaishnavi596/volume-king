"""T09 v2 finite integration tests; synthetic source, no provider or server."""
import ast
import hashlib
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "stage_oracle_t09_canonical_joint_v2_20261118.py"
spec = importlib.util.spec_from_file_location("t09_joint_v2", SCRIPT)
stage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage)

FAKE = '''
def create_app(pairing_key="demo"):
    import datetime
    published = []
    persisted = []
    def _assessment_bars_completed(rows, minutes):
        return len(rows) == 2 and rows[0][0] < rows[1][0] and minutes in (1, 3, 5)
    def persist_candle_cache():
        persisted.append(True)
    def cached_candles(symbol, interval):
        publish(current_scope(pairing_key), symbol, "candle", {
            "bars": [], "observed_at": None, "interval": interval,
            "freshness": "historical_unverified", "signal_eligible": False
        }, timeframe=interval)
    def dhan_intraday(mode):
        if mode == 0:
            return {"symbol":"NIFTY","source":"dhan","interval":"1m","bars":[[1,2],[2,3]],"freshness":"historical_unverified","live_orders_enabled":False}
        if mode == 1:
            row = {
                "bars": [[1,2],[2,3]], "from_date":"2026-11-18",
                "to_date":"2026-11-18", "observed_at":datetime.datetime(2026,11,18,10).isoformat()
            }
            persist_candle_cache()
            return {"symbol":"NIFTY","source":"dhan","interval":"3m","bars":[[1,2],[2,3]],"freshness":"historical_unverified","live_orders_enabled":False}
        if mode == 2:
            return {"symbol":"NIFTY","source":"dhan","interval":"5m","bars":[],"freshness":"stale_or_missing","live_orders_enabled":False}
        row = {
            "bars": [[1,2],[2,3]], "from_date":"2026-11-18",
            "to_date":"2026-11-18", "observed_at":datetime.datetime(2026,11,18,10).isoformat()
        }
        persist_candle_cache()
        return {"symbol":"NIFTY","source":"dhan","interval":"5m","bars":[[1,2],[2,3]],"freshness":"historical_unverified","live_orders_enabled":False}
    return dhan_intraday, published, persisted
'''


def fixture(source):
    tree = ast.parse(source)
    fn = stage.function(tree, "dhan_intraday")
    ret = sorted((n for n in ast.walk(fn)
                  if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict)),
                 key=lambda x: x.lineno)
    records = sorted(n.lineno for n in ast.walk(fn) if isinstance(n, ast.Dict)
                     and stage.CACHE_RECORD_KEYS.issubset(set(stage.literal_keys(n))))
    persisted = sorted(n.lineno for n in ast.walk(fn)
                       if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                       and n.func.id == "persist_candle_cache")
    return (hashlib.sha256(source.encode()).hexdigest(), tuple(records),
            tuple(persisted), tuple(n.lineno for n in ret),
            (ret[1].lineno, ret[3].lineno))


class T09JointCandidateTests(unittest.TestCase):
    def setUp(self):
        self.old = (stage.EXPECTED_SHA, stage.RECORD_LINES, stage.PERSIST_LINES,
                    stage.ALL_RETURNS, stage.PUBLISH_RETURN_LINES)

    def tearDown(self):
        (stage.EXPECTED_SHA, stage.RECORD_LINES, stage.PERSIST_LINES,
         stage.ALL_RETURNS, stage.PUBLISH_RETURN_LINES) = self.old

    def configure(self, source=FAKE):
        (stage.EXPECTED_SHA, stage.RECORD_LINES, stage.PERSIST_LINES,
         stage.ALL_RETURNS, stage.PUBLISH_RETURN_LINES) = fixture(source)

    def test_joint_contract_two_producers_five_keys_and_untouched_returns(self):
        self.configure()
        patched = stage.stage_source(FAKE)
        ast.parse(patched)
        namespace = {"__name__": "__main__"}
        exec(compile(patched, "<t09-synthetic>", "exec"), namespace)
        records = []
        mod_state = types.ModuleType("assessment_state")
        mod_state.publish = lambda scope, symbol, kind, payload, timeframe: records.append(
            (scope, symbol, kind, payload, timeframe))
        mod_scope = types.ModuleType("assessment_scope")
        mod_scope.current_scope = lambda key: key
        with patch.dict(sys.modules, {"assessment_state": mod_state,
                                      "assessment_scope": mod_scope}):
            route, _, persisted = namespace["create_app"]()
            for mode in (0, 1, 2, 3):
                response = route(mode)
                self.assertEqual(tuple(response), stage.RETURN_KEYS)
            self.assertEqual(len(persisted), 2)
        self.assertEqual(len(records), 2)
        for account, symbol, kind, payload, tf in records:
            self.assertEqual(account, "demo")
            self.assertEqual(kind, "candle")
            self.assertEqual(tuple(payload), stage.CANONICAL_FIELDS)
            self.assertFalse(payload["signal_eligible"])
            self.assertEqual(payload["freshness"], "historical_unverified")
            self.assertEqual(payload["interval"], tf)
            self.assertEqual(payload["observed_at"], "2026-11-18T10:00:00")
        self.assertEqual([x[-1] for x in records], ["3m", "5m"])

    def test_missing_assessment_imports_do_not_break_dhan_response(self):
        self.configure()
        namespace = {"__name__": "__main__"}
        exec(compile(stage.stage_source(FAKE), "<t09-synthetic>", "exec"),
             namespace)
        route, _, _ = namespace["create_app"]()
        # Simulate Assessment being absent; intraday history must still succeed.
        with patch.dict(sys.modules, {"assessment_state": None,
                                      "assessment_scope": None}):
            response = route(1)
        self.assertEqual(response["symbol"], "NIFTY")
        self.assertEqual(response["interval"], "3m")
        self.assertEqual(response["freshness"], "historical_unverified")
        self.assertEqual(tuple(response), stage.RETURN_KEYS)

    def test_source_drift_holds(self):
        self.configure()
        with self.assertRaisesRegex(ValueError, "SOURCE_SHA_MISMATCH"):
            stage.stage_source(FAKE + "\n# drift")

    def test_isoformat_missing_holds_without_staging(self):
        bad = FAKE.replace("datetime.datetime(2026,11,18,10).isoformat()",
                           '"not_verified"')
        self.configure(bad)
        with self.assertRaisesRegex(ValueError, "OBSERVATION_NOT_ISOFORMAT"):
            stage.stage_source(bad)

    def test_stale_payload_can_never_publish(self):
        source = FAKE.replace(
            '"interval":"5m","bars":[[1,2],[2,3]],"freshness":"historical_unverified"',
            '"interval":"5m","bars":[[1,2],[2,3]],"freshness":"stale_or_missing"',
        )
        self.configure(source)
        patched = stage.stage_source(source)
        namespace = {"__name__": "__main__"}
        exec(compile(patched, "<t09-synthetic>", "exec"), namespace)
        records = []
        state = types.ModuleType("assessment_state")
        state.publish = lambda *args, **kwargs: records.append(args)
        scope = types.ModuleType("assessment_scope")
        scope.current_scope = lambda key: key
        with patch.dict(sys.modules, {"assessment_state":state,"assessment_scope":scope}):
            route, _, _ = namespace["create_app"]()
            route(3)
        self.assertEqual(records, [])


if __name__ == "__main__":
    unittest.main()
