"""Contract tests for the Oracle GET-only source/runtime snapshot probe."""
import importlib.util
from pathlib import Path
import unittest
from unittest import mock

SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "audit_oracle_collector_runtime_readonly.py"


def module():
    spec = importlib.util.spec_from_file_location("collector_runtime_audit", SOURCE)
    obj = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = obj
    spec.loader.exec_module(obj)
    return obj


class Response:
    def __init__(self, payload):
        import json
        self._data = json.dumps(payload).encode()
        self.status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, n):
        return self._data[:n]


class Opener:
    def __init__(self, payload):
        self.payload = payload
        self.requests = []

    def open(self, req, timeout=0):
        self.requests.append(req)
        self.timeout = timeout
        return Response(self.payload)


class OracleCollectorRuntimeAuditTests(unittest.TestCase):
    def test_no_protected_request_without_operator_key(self):
        a = module()
        opener = Opener({"status": "ok"})
        missing = a.request_get("/v2/snapshot", None, opener=opener)
        self.assertEqual(missing.http, 0)
        self.assertEqual(opener.requests, [])
        health = a.request_get("/health", None, opener=opener)
        self.assertEqual(health.http, 200)
        self.assertEqual(health.body, {"status": "ok"})
        self.assertEqual(health.route, "/health")

    def test_only_local_get_allowed_and_secret_not_in_summary(self):
        a = module()
        opener = Opener({"protocol": 2, "quotes": {"RELIANCE": {"ltp": 999999}},
                         "unavailable": [], "age_seconds": 23, "collection_status": "recently_collected",
                         "live_orders_enabled": False})
        result = a.request_get("/v2/snapshot", "highly-private-key", opener=opener)
        self.assertEqual(result.http, 200)
        req = opener.requests[0]
        self.assertEqual(req.get_method(), "GET")
        self.assertEqual(req.full_url, "http://127.0.0.1:8000/v2/snapshot")
        self.assertEqual(req.get_header("X-botking-key"), "highly-private-key")
        self.assertEqual(opener.timeout, 5)
        summary = a.summarize([result])
        import json
        rendered = json.dumps(summary)
        self.assertNotIn("private", rendered)
        self.assertNotIn("999999", rendered)
        self.assertNotIn("RELIANCE", rendered)
        self.assertEqual(summary["equity_quote_count"], 1)
        self.assertEqual(summary["dhan_api_calls_made"], 0)
        self.assertEqual(summary["oracle_production_changed"], False)
        with self.assertRaises(ValueError):
            a.request_get("/dhan/ltp-batch", "highly-private-key", opener=opener)

    def test_status_distinguishes_missing_collector_from_stale_data(self):
        a = module()
        r = a.ProbeResult
        view = a.summarize([
            r("/health", 200, {"status": "ok"}),
            r("/v2/server-readiness", 200, {"collector": {
                "configured_enabled": False, "status": "disabled",
                "interval_seconds": 90, "last_success_age_seconds": None}}),
            r("/v2/snapshot", 200, {"protocol": 2, "quotes": {},
                "unavailable": [], "collection_status": "not_collected",
                "age_seconds": None, "live_orders_enabled": False}),
        ])
        self.assertTrue(view["health_ok"])
        self.assertEqual(view["collector_enabled"], False)
        self.assertEqual(view["collector_status"], "disabled")
        self.assertEqual(view["snapshot_status"], "not_collected")
        self.assertEqual(view["equity_quote_count"], 0)

    def test_unexpected_http_json_shapes_are_not_green_or_crash(self):
        a = module()
        r = a.ProbeResult
        result = a.summarize([
            r("/health", 200, ["unexpected"]),
            r("/v2/server-readiness", 200, ["unexpected"]),
            r("/v2/snapshot", 200, ["unexpected"]),
        ])
        self.assertFalse(result["health_ok"])
        self.assertIsNone(result["collector_enabled"])
        self.assertEqual(result["collector_status"], "unknown")
        self.assertEqual(result["snapshot_status"], "unknown")
        self.assertIsNone(result["equity_quote_count"])
        self.assertIsNone(result["live_orders_enabled"])

    def test_stale_and_403_do_not_pretend_success(self):
        a = module()
        r = a.ProbeResult
        view = a.summarize([
            r("/health", 200, {"status": "ok"}),
            r("/v2/server-readiness", 403, None),
            r("/v2/snapshot", 200, {"protocol": 2, "quotes": {"A": {"price": 99}},
                "unavailable": [], "age_seconds": 500,
                "collection_status": "collection_overdue",
                "live_orders_enabled": False}),
        ])
        self.assertFalse(view["readiness_route_available"])
        self.assertIsNone(view["collector_enabled"])
        self.assertEqual(view["snapshot_status"], "collection_overdue")
        self.assertEqual(view["snapshot_age_seconds"], 500)
        self.assertFalse(view["quote_freshness_exchange_verified"])


if __name__ == "__main__":
    unittest.main()
