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
    def test_oracle_python39_import_compatible_annotation(self):
        # An Oracle host running Python 3.9 cannot evaluate dict | None
        # at import time; this decorator stores the annotation as text.
        import ast
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        self.assertTrue(any(
            isinstance(node, ast.ImportFrom) and node.module == "__future__"
            and any(alias.name == "annotations" for alias in node.names)
            for node in tree.body))
        a = module()
        self.assertEqual(a.ProbeResult.__annotations__["body"], "dict | None")

    def test_protected_audit_does_not_follow_redirect(self):
        a = module()
        handler = a.NoRedirect()
        import urllib.request
        req = urllib.request.Request(
            "http://127.0.0.1:8000/v2/snapshot",
            headers={"X-BotKing-Key": "secret"}, method="GET")
        self.assertIsNone(handler.redirect_request(
            req, None, 302, "Found", {"Location": "https://outside.invalid/"},
            "https://outside.invalid/"))
        with mock.patch.object(a.urllib.request, "build_opener") as build:
            build.return_value.open.side_effect = a.urllib.error.HTTPError(
                req.full_url, 302, "Found", {}, None)
            result = a.request_get("/v2/snapshot", "secret")
            self.assertEqual(result.http, 302)
            handlers = build.call_args.args
            self.assertTrue(any(isinstance(h, a.NoRedirect) for h in handlers))
        self.assertEqual(result.body, None)

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

    def test_snapshot_error_classes_and_deployed_readiness_schema(self):
        a = module()
        r = a.ProbeResult
        cases = (
            ("upstream_http_429", "RATE_LIMIT_429"),
            ("upstream_http_401", "UPSTREAM_ACCESS_DENIED"),
            ("upstream_http_503", "UPSTREAM_UNAVAILABLE"),
            ("upstream_http_418", "UPSTREAM_HTTP_OTHER"),
            ("ingest_unavailable", "INGEST_EXCEPTION"),
            ("raw-secret-must-never-print", "OTHER_ERROR"),
            (None, "NO_RECORDED_ERROR"),
            ({"unexpected": "value"}, "OTHER_ERROR"),
        )
        for error, category in cases:
            with self.subTest(category=category):
                results = [
                    r("/v2/server-readiness", 200, {
                        "market_data": "configured_separately",
                        "scoring_status": "unverified",
                    }),
                    r("/v2/snapshot", 200, {
                        "protocol": 2, "quotes": {},
                        "collection_status": "upstream_error",
                        "error": error, "age_seconds": None,
                        "live_orders_enabled": False,
                    }),
                ]
                view = a.summarize(results)
                self.assertEqual(view["snapshot_error_class"], category)
                self.assertEqual(view["readiness_collector_schema"], "missing_or_other")
                self.assertEqual(view["readiness_market_data_type"], "str")
                self.assertEqual(view["collector_status"], "unknown")
                self.assertEqual(view["equity_quote_count"], 0)
                self.assertNotIn("raw-secret-must-never-print", str(view))
                self.assertFalse(view["quote_freshness_exchange_verified"])

    def test_three_index_assessments_are_sanitized_and_fail_closed(self):
        a = module()
        r = a.ProbeResult
        base = {
            "status": "incomplete",
            "signal_eligible": False,
            "bullish_score": 98.5,
            "factors": {
                "news": {"status": "unavailable", "private_note": "secret-one"},
                "futures": {"status": "available", "bullish": 99},
                "options": {"status": "unavailable"},
                "candle": {"status": "unavailable"},
            },
            "assessment_filters": [
                {"id": "pcr", "status": "available", "value": 1.2},
                {"id": "max_pain", "status": "unavailable"},
            ],
        }
        view = a.summarize([
            r("/v2/assessment/NIFTY", 200, base),
            r("/v2/assessment/BANKNIFTY", 503, None),
            r("/v2/assessment/SENSEX", 200, {
                **base, "factors": "invalid", "assessment_filters": "invalid"
            }),
        ])
        indices = view["index_assessments"]
        self.assertEqual(set(indices), {"NIFTY", "BANKNIFTY", "SENSEX"})
        self.assertEqual(indices["NIFTY"]["assessment_status"], "incomplete")
        self.assertFalse(indices["NIFTY"]["signal_eligible"])
        self.assertEqual(indices["NIFTY"]["factor_statuses"]["futures"], "available")
        self.assertEqual(indices["NIFTY"]["filter_statuses"]["pcr"], "available")
        self.assertEqual(indices["BANKNIFTY"]["assessment_status"], "unknown")
        self.assertEqual(indices["SENSEX"]["factor_statuses"]["news"], "unknown")
        self.assertEqual(indices["SENSEX"]["filter_statuses"]["pcr"], "unknown")
        import json
        output = json.dumps(view)
        self.assertNotIn("secret-one", output)
        self.assertNotIn("98.5", output)
        self.assertNotIn('"bullish"', output)

    def test_assessment_requires_pairing_and_is_local_get(self):
        a = module()
        opener = Opener({"status": "incomplete", "signal_eligible": False})
        self.assertEqual(a.request_get("/v2/assessment/NIFTY", None, opener=opener).http, 0)
        self.assertEqual(opener.requests, [])
        result = a.request_get("/v2/assessment/NIFTY", "private-key", opener=opener)
        self.assertEqual(result.http, 200)
        self.assertEqual(opener.requests[0].get_method(), "GET")
        self.assertEqual(opener.requests[0].full_url,
                         "http://127.0.0.1:8000/v2/assessment/NIFTY")
        with self.assertRaises(ValueError):
            a.request_get("/v2/assessment/RELIANCE", "private-key", opener=opener)

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
