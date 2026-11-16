"""Offline guard tests for sanitized Oracle result classification."""
import importlib.util
from pathlib import Path
import tempfile
import json
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "classify_oracle_audit_results.py"
spec = importlib.util.spec_from_file_location("oracle_audit_classifier", SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def codes(result):
    return [x["code"] for x in result["issues"]]


class OracleAuditClassifierTests(unittest.TestCase):
    def setUp(self):
        self.routes = {"syntax": "PASS", "expected_routes": 9,
                       "source_present": 9, "source_missing": [],
                       "source_sha256": "a" * 64}
        self.filters = {"syntax": "PASS", "assessment_route_source_count": 1,
                        "known_placeholder_detected": True,
                        "source_sha256": "a" * 64}
        self.collector = {"health_http": 200, "health_ok": True,
                          "readiness_http": 200, "collector_enabled": True,
                          "collector_status": "recently_collected",
                          "snapshot_http": 200, "snapshot_protocol": 2,
                          "snapshot_status": "recently_collected",
                          "live_orders_enabled": False}

    def test_green_runtime_still_does_not_prove_five_filters(self):
        out = mod.classify(self.routes, self.filters, self.collector)
        self.assertIn("FIVE_FILTER_PLACEHOLDER", codes(out))
        self.assertFalse(out["runtime_five_filters_proven"])
        self.assertFalse(out["equity_pcr_entitlement_proven"])
        self.assertFalse(out["apk_release_allowed"])
        self.assertEqual(out["orders_sent"], 0)

    def test_recent_label_with_overdue_age_is_not_silent(self):
        self.collector.update(
            collector_interval_seconds=90,
            collector_last_success_age_seconds=550,
            snapshot_age_seconds=500,
        )
        out = mod.classify(self.routes, self.filters, self.collector)
        self.assertIn("SNAPSHOT_AGE_CONFLICT", codes(out))
        self.assertIn("COLLECTOR_AGE_CONFLICT", codes(out))
        self.assertFalse(out["runtime_five_filters_proven"])

    def test_normal_recent_age_does_not_warn(self):
        self.collector.update(
            collector_interval_seconds=90,
            collector_last_success_age_seconds=42,
            snapshot_age_seconds=45,
        )
        out = mod.classify(self.routes, self.filters, self.collector)
        self.assertNotIn("SNAPSHOT_AGE_CONFLICT", codes(out))
        self.assertNotIn("COLLECTOR_AGE_CONFLICT", codes(out))

    def test_recent_snapshot_zero_quote_coverage_is_warning(self):
        self.collector.update(equity_quote_count=0)
        out = mod.classify(self.routes, self.filters, self.collector)
        self.assertIn("SNAPSHOT_EMPTY_QUOTES", codes(out))
        self.assertFalse(out["runtime_five_filters_proven"])

    def test_recent_snapshot_unknown_quote_coverage_is_warning(self):
        self.collector.update(equity_quote_count=None)
        out = mod.classify(self.routes, self.filters, self.collector)
        self.assertIn("SNAPSHOT_QUOTE_COVERAGE_UNKNOWN", codes(out))
        self.collector.update(equity_quote_count=51)
        out = mod.classify(self.routes, self.filters, self.collector)
        self.assertNotIn("SNAPSHOT_QUOTE_COVERAGE_UNKNOWN", codes(out))
        self.assertNotIn("SNAPSHOT_EMPTY_QUOTES", codes(out))

    def test_invalid_matching_hashes_do_not_certify_source(self):
        self.routes["source_sha256"] = "placeholder"
        self.filters["source_sha256"] = "placeholder"
        out = mod.classify(self.routes, self.filters, self.collector)
        self.assertIn("SOURCE_REPORT_MISMATCH", codes(out))
        self.assertFalse(out["source_audit_complete"])

    def test_nonfinite_age_does_not_create_false_freshness_warning(self):
        self.collector.update(collector_interval_seconds=float("nan"),
                              snapshot_age_seconds=10000.0,
                              collector_last_success_age_seconds=10000.0)
        out = mod.classify(self.routes, self.filters, self.collector)
        self.assertNotIn("SNAPSHOT_AGE_CONFLICT", codes(out))
        self.assertNotIn("COLLECTOR_AGE_CONFLICT", codes(out))
        self.assertFalse(out["runtime_five_filters_proven"])

    def test_mixed_version_audit_reports_never_mark_complete(self):
        self.filters["source_sha256"] = "b" * 64
        out = mod.classify(self.routes, self.filters, self.collector)
        self.assertIn("SOURCE_REPORT_MISMATCH", codes(out))
        self.assertFalse(out["source_audit_complete"])
        self.assertFalse(out["apk_release_allowed"])

    def test_missing_routes_never_mark_source_audit_complete(self):
        self.routes["source_present"] = 8
        self.routes["source_missing"] = ["/v2/assessment/{symbol}"]
        out = mod.classify(self.routes, self.filters, self.collector)
        self.assertFalse(out["source_audit_complete"])
        self.assertIn("SOURCE_ROUTES_MISSING", codes(out))

    def test_valid_source_count_does_not_imply_producer(self):
        out = mod.classify(self.routes, self.filters, self.collector)
        self.assertTrue(out["source_audit_complete"])
        self.assertFalse(out["runtime_five_filters_proven"])

    def test_missing_and_auth_are_distinct(self):
        self.routes["source_missing"] = ["/v2/assessment/{symbol}"]
        self.routes["source_present"] = 8
        self.collector["readiness_http"] = 403
        self.collector["snapshot_http"] = 404
        result = mod.classify(self.routes, self.filters, self.collector)
        self.assertIn("SOURCE_ROUTES_MISSING", codes(result))
        self.assertIn("AUTH_DENIED", codes(result))
        self.assertIn("LIVE_ROUTE_MISSING", codes(result))

    def test_disabled_collector_and_stale_snapshot(self):
        self.collector.update(collector_enabled=False, collector_status="disabled",
                              snapshot_status="collection_overdue")
        out = mod.classify(self.routes, self.filters, self.collector)
        self.assertIn("COLLECTOR_DISABLED", codes(out))
        self.assertIn("SNAPSHOT_NOT_CURRENTLY_COLLECTED", codes(out))

    def test_nonplaceholder_is_unknown_not_pass(self):
        self.filters["known_placeholder_detected"] = False
        out = mod.classify(self.routes, self.filters, self.collector)
        self.assertIn("ASSESSMENT_IMPLEMENTATION_UNKNOWN", codes(out))
        self.assertFalse(out["runtime_five_filters_proven"])

    def test_missing_key_and_429_distinct(self):
        self.collector.update(readiness_http=0, snapshot_http=429)
        out = mod.classify(self.routes, self.filters, self.collector)
        self.assertIn("RUNTIME_NOT_VERIFIED", codes(out))
        self.assertIn("RATE_LIMIT", codes(out))

    def test_malformed_reports_fail_closed(self):
        with self.assertRaises(ValueError):
            mod.classify([], self.filters, self.collector)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "data.json"
            p.write_text(json.dumps([{"bad": 1}]))
            with self.assertRaises(ValueError):
                mod.read_report(p)
            p.write_text(json.dumps(self.routes))
            self.assertEqual(mod.read_report(p), self.routes)
            link = Path(tmp) / "link.json"
            link.symlink_to(p)
            with self.assertRaises(ValueError):
                mod.read_report(link)


if __name__ == "__main__":
    unittest.main()
