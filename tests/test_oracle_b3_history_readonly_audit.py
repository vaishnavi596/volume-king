"""Offline-only B3 Oracle source parity preflight contract checks."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_oracle_b3_history_readonly.py"


def audit_module():
    spec = importlib.util.spec_from_file_location("b3_history_audit", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class B3OracleHistorySourceAuditTests(unittest.TestCase):
    def test_github_server_source_is_ready_for_manual_review_not_runtime_proven(self):
        outcome = audit_module().audit(ROOT / "backend" / "server.py")
        self.assertEqual(outcome["syntax"], "PASS")
        self.assertTrue(outcome["source_ready_for_manual_review"], outcome)
        self.assertFalse(outcome["runtime_verified"])
        self.assertFalse(outcome["oracle_deployed_verified"])
        self.assertFalse(outcome["production_changed"])

    def test_route_without_guard_does_not_pass(self):
        source = ('def create_app():\n'
                  '    @app.post("/dhan/intraday")\n'
                  '    def fetch(body):\n'
                  '        return {}\n')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "server.py"
            path.write_text(source, encoding="utf-8")
            outcome = audit_module().audit(path)
        self.assertTrue(outcome["source_checks"]["one_intraday_post_route"])
        self.assertFalse(outcome["source_checks"]["route_guarded_by_history_singleflight"])
        self.assertFalse(outcome["source_ready_for_manual_review"])

    def test_nonreentrant_lane_fails_source_parity(self):
        a = audit_module()
        with tempfile.TemporaryDirectory() as directory:
            source = (ROOT / "backend" / "server.py").read_text(encoding="utf-8")
            self.assertIn("history_miss_locks = tuple(threading.RLock()", source)
            path = Path(directory) / "server.py"
            path.write_text(source.replace(
                "history_miss_locks = tuple(threading.RLock()",
                "history_miss_locks = tuple(threading.Lock()"), encoding="utf-8")
            result = a.audit(path)
        self.assertFalse(result["source_checks"]["singleflight_reentrant_locks"])
        self.assertFalse(result["source_ready_for_manual_review"])

    def test_reject_symlink_before_reading(self):
        with tempfile.TemporaryDirectory() as directory:
            original = Path(directory) / "normal.py"
            original.write_text("pass\n", encoding="utf-8")
            link = Path(directory) / "server.py"
            link.symlink_to(original)
            with self.assertRaisesRegex(ValueError, "non-symlink"):
                audit_module().audit(link)


if __name__ == "__main__":
    unittest.main()
