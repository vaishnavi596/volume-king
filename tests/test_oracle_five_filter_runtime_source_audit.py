"""Offline tests for read-only Oracle assessment source inspection."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_oracle_five_filters_readonly.py"
spec = importlib.util.spec_from_file_location("oracle_filter_audit", SCRIPT)
audit_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_module)


class FiveFilterOracleReadOnlyAuditTests(unittest.TestCase):
    def test_repository_source_is_explicit_placeholder_not_usable_scores(self):
        data = audit_module.audit(ROOT / "backend" / "server.py")
        self.assertEqual(data["syntax"], "PASS")
        self.assertEqual(data["assessment_route_source_count"], 1)
        self.assertTrue(data["known_placeholder_detected"])
        self.assertTrue(data["five_filter_ids_in_route_source"])
        self.assertTrue(data["four_factor_ids_in_route_source"])
        self.assertFalse(data["producer_proven_functional"])
        self.assertFalse(data["deployed_runtime_route_verified"])
        self.assertEqual(data["dhan_requests_made"], 0)

    def test_missing_route_is_not_assumed_to_work(self):
        with TemporaryDirectory() as d:
            path = Path(d) / "server.py"
            path.write_text("app = object()\n", encoding="utf-8")
            result = audit_module.audit(path)
        self.assertEqual(result["assessment_route_source_count"], 0)
        self.assertFalse(result["known_placeholder_detected"])
        self.assertFalse(result["five_filter_ids_in_route_source"])

    def test_different_route_is_unknown_not_functional_proof(self):
        with TemporaryDirectory() as d:
            path = Path(d) / "server.py"
            path.write_text(
                'def source():\n'
                '    @app.get("/v2/assessment/{symbol}")\n'
                '    def assessment(symbol):\n'
                '        return {"symbol": symbol, "status": "ready"}\n',
                encoding="utf-8",
            )
            result = audit_module.audit(path)
        self.assertEqual(result["assessment_route_source_count"], 1)
        self.assertFalse(result["known_placeholder_detected"])
        self.assertFalse(result["producer_proven_functional"])

    def test_unrelated_object_get_is_not_oracle_app_route(self):
        with TemporaryDirectory() as d:
            path = Path(d) / "server.py"
            path.write_text(
                'def source():\n'
                '    @other.get("/v2/assessment/{symbol}")\n'
                '    def assessment(symbol):\n'
                '        return {"status": "not_configured"}\n',
                encoding="utf-8",
            )
            result = audit_module.audit(path)
        self.assertEqual(result["assessment_route_source_count"], 0)
        self.assertFalse(result["known_placeholder_detected"])
        self.assertFalse(result["producer_proven_functional"])

    def test_symlink_is_never_followed(self):
        with TemporaryDirectory() as d:
            target = Path(d) / "source.py"
            target.write_text("pass\n", encoding="utf-8")
            alias = Path(d) / "server.py"
            alias.symlink_to(target)
            with self.assertRaises(ValueError):
                audit_module.audit(alias)


if __name__ == "__main__":
    unittest.main()
