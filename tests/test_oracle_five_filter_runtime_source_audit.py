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

    def test_allowlisted_reason_placeholder_is_recognized_without_legacy_prose(self):
        with TemporaryDirectory() as d:
            path = Path(d) / "server.py"
            path.write_text(
                'def create_app():\n'
                '    @app.get("/v2/assessment/{symbol}")\n'
                '    def assessment(symbol):\n'
                '        ids = ("oi_support", "oi_resistance", "max_pain", "pcr", "candle_trend")\n'
                '        factors = ("news", "futures", "options", "candle")\n'
                '        return {"collection_status": "not_configured",\n'
                '                "assessment_filters": [{"id": key, "status": "unavailable",\n'
                '                                        "reason": "not_configured"} for key in ids],\n'
                '                "factors": factors, "signal_eligible": False}\n',
                encoding="utf-8",
            )
            data = audit_module.audit(path)
        self.assertTrue(data["known_placeholder_detected"])
        self.assertFalse(data["producer_proven_functional"])

    def test_not_configured_without_unavailable_does_not_count_as_placeholder(self):
        with TemporaryDirectory() as d:
            path = Path(d) / "server.py"
            path.write_text(
                'def create_app():\n'
                '    @app.get("/v2/assessment/{symbol}")\n'
                '    def assessment(symbol):\n'
                '        return {"status": "not_configured", "reason": "not_configured"}\n',
                encoding="utf-8",
            )
            data = audit_module.audit(path)
        self.assertFalse(data["known_placeholder_detected"])

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

    def test_oracle_delegated_assessment_module_is_detected_without_execution(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            (root / "server.py").write_text(
                "def create_app():\n"
                "    register_assessment_routes(app, pairing_key)\n",
                encoding="utf-8")
            (root / "assessment_api.py").write_text(
                "def register_assessment_routes(app, pairing_key):\n"
                "    @app.get('/v2/assessment/{symbol}')\n"
                "    def assessment(symbol):\n"
                "        return read(scope, symbol)\n",
                encoding="utf-8")
            result = audit_module.audit(root / "server.py")
        self.assertEqual(result["assessment_route_source_count"], 0)
        self.assertTrue(result["effective_route_source_found"])
        self.assertTrue(result["delegated_assessment"]["register_call_present"])
        self.assertTrue(result["delegated_assessment"]["module_route_present"])
        self.assertTrue(result["delegated_assessment"]["cache_read_wired"])
        self.assertFalse(result["deployed_runtime_route_verified"])

    def test_non_registered_or_symlink_module_is_not_accepted(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            (root / "server.py").write_text("pass\n", encoding="utf-8")
            (root / "assessment_api.py").write_text(
                "@app.get('/v2/assessment/{symbol}')\n"
                "def assessment(symbol):\n"
                "    return read(scope, symbol)\n", encoding="utf-8")
            result = audit_module.audit(root / "server.py")
            self.assertFalse(result["effective_route_source_found"])
            self.assertFalse(result["delegated_assessment"]["register_call_present"])
            (root / "server.py").write_text(
                "def create_app():\n"
                "    register_assessment_routes(app, pairing_key)\n", encoding="utf-8")
            (root / "assessment_api.py").unlink()
            (root / "assessment_api.py").symlink_to(root / "server.py")
            result = audit_module.audit(root / "server.py")
            self.assertFalse(result["effective_route_source_found"])
            self.assertFalse(result["delegated_assessment"]["module_route_present"])

    def test_unrelated_registration_and_unscoped_module_route_fail_closed(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            (root / "server.py").write_text(
                "def not_the_factory():\n"
                "    register_assessment_routes(app, pairing_key)\n"
                "def create_app():\n"
                "    return app\n", encoding="utf-8")
            (root / "assessment_api.py").write_text(
                "def register_assessment_routes(app, pairing_key):\n"
                "    return None\n"
                "@app.get('/v2/assessment/{symbol}')\n"
                "def unrelated(symbol):\n"
                "    return read(scope, symbol)\n", encoding="utf-8")
            result = audit_module.audit(root / "server.py")
            self.assertFalse(result["delegated_assessment"]["register_call_present"])
            self.assertFalse(result["effective_route_source_found"])
            (root / "server.py").write_text(
                "def create_app():\n"
                "    register_assessment_routes(app, pairing_key)\n", encoding="utf-8")
            result = audit_module.audit(root / "server.py")
            self.assertTrue(result["delegated_assessment"]["register_call_present"])
            self.assertFalse(result["delegated_assessment"]["module_route_present"])
            self.assertFalse(result["effective_route_source_found"])

    def test_evidence_writer_publish_and_ttl_static_audit(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            (root / "server.py").write_text(
                "def create_app():\n"
                "    candle_cache = {}\n"
                "    candle_cache[(symbol, interval)] = {'bars': []}\n"
                "    if interval == '5' and bars:\n"
                "        publish(scope, symbol, 'candle', {'bars': bars})\n"
                "    publish(scope, symbol, 'options', {'option_metrics': {}})\n",
                encoding="utf-8")
            (root / "assessment_state.py").write_text(
                "_TTL = 180\n", encoding="utf-8")
            result = audit_module.audit(root / "server.py")["evidence_wiring"]
        self.assertEqual(len(result["candle_cache_writer_lines"]), 1)
        self.assertEqual(len(result["candle_publish_lines"]), 1)
        self.assertEqual(len(result["five_minute_candle_publish_guard_lines"]), 1)
        self.assertEqual(len(result["options_publish_lines"]), 1)
        self.assertEqual(result["assessment_state_ttl_seconds"], 180)
        self.assertFalse(result["runtime_evidence_verified"])
        self.assertFalse(result["production_changed"])

    def test_assessment_state_kind_only_key_cannot_pass_timeframe_gate(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            (root / "server.py").write_text("def create_app(): pass\n", encoding="utf-8")
            state = root / "assessment_state.py"
            state.write_text(
                "def publish(scope, symbol, kind, value):\n"
                "    cache[(scope, symbol, kind)] = value\n",
                encoding="utf-8")
            result = audit_module.audit(root / "server.py")["evidence_wiring"]
            evidence = result["assessment_state_key_evidence"]
            self.assertEqual(evidence["write_key_dimensions"], [["scope", "symbol", "kind"]])
            self.assertIs(evidence["timeframe_separated"], False)
            state.write_text(
                "def publish(scope, symbol, kind, timeframe, value):\n"
                "    cache[(scope, symbol, kind, timeframe)] = value\n",
                encoding="utf-8")
            evidence = audit_module.audit(root / "server.py")["evidence_wiring"]["assessment_state_key_evidence"]
            self.assertTrue(evidence["timeframe_separated"])
            state.write_text("def publish(scope, symbol, kind, value): pass\n", encoding="utf-8")
            evidence = audit_module.audit(root / "server.py")["evidence_wiring"]["assessment_state_key_evidence"]
            self.assertIsNone(evidence["timeframe_separated"])

    def test_missing_state_and_unconditional_publish_are_not_assumed_live(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            (root / "server.py").write_text(
                "def create_app():\n"
                "    publish(scope, symbol, 'candle', {'bars': bars})\n",
                encoding="utf-8")
            result = audit_module.audit(root / "server.py")["evidence_wiring"]
        self.assertEqual(result["five_minute_candle_publish_guard_lines"], [])
        self.assertIsNone(result["assessment_state_ttl_seconds"])
        self.assertFalse(result["mapping_route_direct_in_server"])
        self.assertFalse(result["runtime_evidence_verified"])

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
