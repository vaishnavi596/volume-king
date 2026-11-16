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
        self.assertIn("def snapshot():\\n        return {}", output)
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

    def test_rejects_missing_anchor(self):
        source = SOURCE.replace(b'/v2/snapshot', b'/v2/other')
        with patch.object(module, "EXPECTED_SHA", hashlib.sha256(source).hexdigest()):
            with self.assertRaisesRegex(ValueError, "anchor route missing"):
                module.prepare(source)

if __name__ == "__main__":
    unittest.main()
