"""Offline, no-Dhan safety tests for create-only Oracle route candidate."""
import hashlib
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "oracle_assessment_candidate", ROOT / "scripts" / "prepare_oracle_assessment_routes_candidate.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

SOURCE = b'''from typing import Optional
def create_app():
    @app.get("/v2/snapshot")
    def snapshot():
        return {}
'''

class OracleAssessmentCandidateTests(unittest.TestCase):
    def test_rejects_wrong_sha(self):
        with self.assertRaisesRegex(ValueError, "SHA mismatch"):
            module.prepare(SOURCE)

    def test_inserts_two_routes_and_preserves_existing_source(self):
        with patch.object(module, "EXPECTED_SHA", hashlib.sha256(SOURCE).hexdigest()):
            candidate = module.prepare(SOURCE)
        output = candidate.decode()
        self.assertIn("def snapshot():\n        return {}", output)
        self.assertIn('"/v2/server-readiness"', output)
        self.assertIn('"/v2/assessment/{symbol}"', output)
        self.assertIn('"not_configured"', output)
        self.assertIn('"live_orders_enabled": False', output)
        self.assertIn('"bullish_score": None', output)
        self.assertEqual(output.count('@app.get("/v2/snapshot")'), 1)

    def test_rejects_duplicate_target(self):
        source = SOURCE.replace(b'    @app.get("/v2/snapshot")',
                                b'    @app.get("/v2/assessment/{symbol}")\n'
                                b'    def existing(symbol): return {}\n'
                                b'    @app.get("/v2/snapshot")')
        with patch.object(module, "EXPECTED_SHA", hashlib.sha256(source).hexdigest()):
            with self.assertRaisesRegex(ValueError, "already present"):
                module.prepare(source)

    def test_rejects_oracle_delegated_assessment_and_readiness_routes(self):
        for registered in ("register_assessment_routes", "register_readiness_routes"):
            source = SOURCE.replace(
                b"    @app.get(\"/v2/snapshot\")",
                ("    " + registered + "(app, pairing_key)\\n").encode()
                .replace(b"\\n", b"\n")
                + b"    @app.get(\"/v2/snapshot\")")
            with self.subTest(registered=registered):
                with patch.object(module, "EXPECTED_SHA",
                                  hashlib.sha256(source).hexdigest()):
                    with self.assertRaisesRegex(ValueError, "Delegated .* registered"):
                        module.prepare(source)

    def test_mapping_only_candidate_is_protected_and_not_an_option_entitlement(self):
        source = (
            b"from typing import Optional\n"
            b"DYNAMIC_INSTRUMENTS = {}\n"
            b"def create_app():\n"
            b"    register_assessment_routes(app, pairing_key)\n"
        )
        with patch.object(module, "EXPECTED_SHA", hashlib.sha256(source).hexdigest()):
            candidate = module.prepare_mapping_only(source)
        body = candidate.decode()
        self.assertIn('"/v2/option-underlying-status/{symbol}"', body)
        self.assertIn('hmac.compare_digest', body)
        self.assertIn('"mapping_only"', body)
        self.assertIn('"expiry_verified": False', body)
        self.assertIn('"chain_verified": False', body)
        self.assertIn('"pcr_verified": False', body)
        self.assertIn('"broker_requests": 0', body)
        self.assertNotIn('DhanFeed(', body)
        with patch.object(module, "EXPECTED_SHA", hashlib.sha256(candidate).hexdigest()):
            with self.assertRaisesRegex(ValueError, "already declared"):
                module.prepare_mapping_only(candidate)

    def test_mapping_only_rejects_missing_registration_and_wrong_hash(self):
        source = b"DYNAMIC_INSTRUMENTS = {}\ndef create_app():\n    pass\n"
        with self.assertRaisesRegex(ValueError, "SHA mismatch"):
            module.prepare_mapping_only(source)
        with patch.object(module, "EXPECTED_SHA", hashlib.sha256(source).hexdigest()):
            with self.assertRaisesRegex(ValueError, "registered assessment"):
                module.prepare_mapping_only(source)

    def test_mapping_only_runtime_http_auth_and_broker_free(self):
        """Execute only a synthetic candidate in an offline TestClient."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        source = b'''import hmac
from typing import Optional
from fastapi import FastAPI, Header, HTTPException

DYNAMIC_INSTRUMENTS = {
    "HDFCBANK": ("NSE_EQ", 1333, "EQUITY"),
    "NIFTY": ("IDX_I", 13, "INDEX"),
    "BOGUS": ("NSE_EQ", True, "EQUITY"),
}
def register_assessment_routes(app, pairing_key):
    pass

def create_app():
    app = FastAPI()
    pairing_key = "k" * 40
    register_assessment_routes(app, pairing_key)
    return app
'''
        with patch.object(module, "EXPECTED_SHA", hashlib.sha256(source).hexdigest()):
            candidate = module.prepare_mapping_only(source)
        ns = {"__name__": "offline_mapping_candidate"}
        exec(compile(candidate, "<offline-mapping-only>", "exec"), ns)
        app = ns["create_app"]()
        client = TestClient(app)
        path = "/v2/option-underlying-status/HDFCBANK"
        self.assertEqual(client.get(path).status_code, 403)
        response = client.get(path, headers={"X-BotKing-Key": "k" * 40})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["symbol"], "HDFCBANK")
        self.assertTrue(data["mapped"])
        self.assertEqual(data["status"], "mapping_only")
        self.assertFalse(data["expiry_verified"])
        self.assertFalse(data["chain_verified"])
        self.assertFalse(data["pcr_verified"])
        self.assertEqual(data["broker_requests"], 0)
        self.assertFalse(data["live_orders_enabled"])
        assert client.get("/v2/option-underlying-status/NIFTY",
                          headers={"X-BotKing-Key": "k" * 40}).json()["mapped"]
        for symbol in ("UNKNOWN", "BOGUS"):
            result = client.get("/v2/option-underlying-status/" + symbol,
                                headers={"X-BotKing-Key": "k" * 40})
            self.assertEqual(result.status_code, 200)
            self.assertFalse(result.json()["mapped"])
        self.assertEqual(client.get("/v2/option-underlying-status/bad%20symbol",
                                    headers={"X-BotKing-Key": "k" * 40}).status_code, 422)

    def test_rejects_snapshot_route_outside_create_app(self):
        source = SOURCE.replace(b"def create_app():", b"def different_factory():")
        with patch.object(module, "EXPECTED_SHA", hashlib.sha256(source).hexdigest()):
            with self.assertRaisesRegex(ValueError, "directly inside create_app"):
                module.prepare(source)

    def test_rejects_missing_anchor(self):
        source = SOURCE.replace(b'/v2/snapshot', b'/v2/other')
        with patch.object(module, "EXPECTED_SHA", hashlib.sha256(source).hexdigest()):
            with self.assertRaisesRegex(ValueError, "anchor route missing"):
                module.prepare(source)

if __name__ == "__main__":
    unittest.main()
