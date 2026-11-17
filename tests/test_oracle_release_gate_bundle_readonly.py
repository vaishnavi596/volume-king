"""Offline fail-closed contract for the grouped Oracle evidence collector."""
import tempfile
import unittest
from pathlib import Path

from scripts.audit_oracle_release_gate_bundle_readonly import collect, RELEASE_GATE_PATHS
from scripts.audit_oracle_collector_runtime_readonly import PATHS as COLLECTOR_PATHS
from scripts.audit_oracle_collector_runtime_readonly import ProbeResult
from test_oracle_s18_watchlist_patch import FIXTURE
from scripts.oracle_s18_watchlist_patch import make_stage


class OracleBundleTests(unittest.TestCase):
    def test_release_gate_three_get_allowlist_is_independent_of_index_diagnostic(self):
        self.assertEqual(RELEASE_GATE_PATHS, (
            "/health", "/v2/server-readiness", "/v2/snapshot"))
        self.assertEqual(len(RELEASE_GATE_PATHS), 3)
        self.assertEqual(len(COLLECTOR_PATHS), 6)
        self.assertTrue(all(path in COLLECTOR_PATHS for path in RELEASE_GATE_PATHS))

    def test_source_signatures_and_bounded_three_gets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            server = root / "server.py"
            server.write_text("from fastapi import FastAPI\napp = FastAPI()\n", encoding="utf-8")
            watch = root / "watchlist_store.py"
            watch.write_text(make_stage(FIXTURE), encoding="utf-8")
            calls = []

            def fake_get(path, key):
                calls.append((path, key))
                bodies = {
                    "/health": {"status": "ok", "live_orders_enabled": False},
                    "/v2/server-readiness": {"collector": {"status": "disabled", "configured_enabled": False}},
                    "/v2/snapshot": {"protocol": 2, "quotes": {}, "unavailable": [],
                                     "live_orders_enabled": False},
                }
                return ProbeResult(path, 200, bodies[path])

            data = collect(pairing_key="fixture-only-not-real", server_path=server,
                           watchlist_path=watch, http_get=fake_get)
            self.assertEqual([x[0] for x in calls], [
                "/health", "/v2/server-readiness", "/v2/snapshot"])
            self.assertTrue(data["watchlist_s18_source"]["details"]["global_70_source_signature"])
            self.assertFalse(data["routes_source"]["details"]["runtime_routes_verified"])
            self.assertFalse(data["assessment_source"]["details"]["producer_proven_functional"])
            self.assertTrue(data["runtime_readonly_get"]["health_ok"])
            self.assertFalse(data["release_ready"])
            self.assertFalse(data["production_changed"])
            self.assertFalse(data["watchlist_saved_json_read"])
            self.assertEqual(data["direct_dhan_api_requests"], 0)
            self.assertEqual(data["orders_attempted"], 0)
            self.assertFalse(data["exchange_freshness_verified"])

    def test_missing_files_fail_closed_without_path_or_secret_echo(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.py"
            calls = []
            def fake_get(route, key):
                calls.append(route)
                return ProbeResult(route, 0, None)
            data = collect(pairing_key=None, server_path=path,
                           watchlist_path=path, http_get=fake_get)
            for name in ("routes_source", "assessment_source", "watchlist_s18_source"):
                self.assertEqual(data[name]["status"], "UNAVAILABLE")
                self.assertNotIn("details", data[name])
            self.assertEqual(len(calls), 3)
            self.assertFalse(data["release_ready"])
            self.assertIsNone(data["runtime_readonly_get"]["live_orders_enabled"])


if __name__ == "__main__":
    unittest.main()
