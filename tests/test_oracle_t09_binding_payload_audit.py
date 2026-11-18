"""Isolated AST tests: T09 Oracle source audit has no IO side effects."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from scripts.audit_oracle_t09_binding_payload_readonly import inspect

SERVER = '''
def create_app():
    def current_scope(key):
        return "s"
    def publish(scope, symbol, kind, value, timeframe=None):
        return None
    def _assessment_bars_completed(rows, minutes):
        return True
    def cached_candles(symbol, interval, x_botking_key):
        entry = {"bars": [(1,2,3,4,5)]}
        publish(current_scope("k"), symbol, "candle",
                {"bars": [list(bar) for bar in entry.get("bars", [])]},
                timeframe=interval)
    def dhan_intraday(body, x_botking_key):
        if body:
            return {"symbol": "NIFTY", "interval":"1", "bars": [],
                    "freshness":"historical_unverified"}
        return {"symbol":"NIFTY", "interval":"3", "bars": [],
                "freshness":"stale"}
'''
STAGED = SERVER.replace(
    '    def dhan_intraday(body, x_botking_key):',
    '    def dhan_intraday(body, x_botking_key):\n'
    '        def _bk_publish_completed_intraday(response):\n'
    '            publish(current_scope("k"), response["symbol"], "candle",\n'
    '                    {"bars": response["bars"]}, timeframe="1m")\n'
    '            return response',
)
STATE = '''
def publish(scope, symbol, kind, value, timeframe=None, expiry=None):
    key = (scope, symbol, timeframe, expiry)
    _cache[key] = value

def read(scope, symbol, timeframe=None, expiry=None):
    key = (scope, symbol, timeframe, expiry)
    return _cache[key]
'''
API = '''
def assessment(symbol, timeframe=None, expiry=None):
    return read(scope, symbol, timeframe=timeframe, expiry=expiry)
'''


class T09BindingPayloadAuditTests(unittest.TestCase):
    def test_ast_shape_and_scope_without_importing_runtime(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            files = {"server.py": SERVER, "assessment_state.py": STATE,
                     "assessment_api.py": API}
            for name, content in files.items():
                (directory / name).write_text(content, encoding="utf-8")
            candidate = directory / "candidate.py"
            candidate.write_text(STAGED, encoding="utf-8")
            expected = {name: hashlib.sha256(content.encode()).hexdigest()
                        for name, content in files.items()}
            report = inspect(directory, candidate, expected,
                             hashlib.sha256(STAGED.encode()).hexdigest())
            self.assertEqual(report["status"], "SOURCE_INSPECTION_ONLY")
            self.assertEqual(report["payload"]["canonical"]["kind"], "dict")
            self.assertEqual(report["payload"]["staged"]["keys"], ["bars"])
            self.assertEqual(len(report["payload"]["original_return_shapes"]), 2)
            self.assertEqual(report["http_requests"], 0)
            self.assertEqual(report["dhan_requests"], 0)
            self.assertFalse(report["production_changed"])
            bindings = report["binding"]["dhan_intraday"]["visible_bindings"]
            self.assertTrue(any("publish" in x["defines"] for x in bindings))

    def test_sha_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            for name in ("server.py", "assessment_state.py", "assessment_api.py"):
                (directory / name).write_text("pass\n")
            candidate = directory / "candidate.py"
            candidate.write_text("pass\n")
            with self.assertRaisesRegex(ValueError, "SOURCE_SHA_MISMATCH"):
                inspect(directory, candidate, {n: "not_sha" for n in (
                    "server.py", "assessment_state.py", "assessment_api.py")},
                    "not_sha")

    def test_missing_candidate_refused(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            files = {"server.py": SERVER, "assessment_state.py": STATE,
                     "assessment_api.py": API}
            for name, content in files.items():
                (directory / name).write_text(content, encoding="utf-8")
            hashes = {n: hashlib.sha256(x.encode()).hexdigest() for n, x in files.items()}
            with self.assertRaisesRegex(ValueError, "CANDIDATE_MISSING"):
                inspect(directory, directory / "missing.py", hashes, "none")


if __name__ == "__main__":
    unittest.main()
