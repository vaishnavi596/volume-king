"""Offline safety tests for the read-only Oracle dependency preflight."""
import hashlib
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / "scripts" / "audit_oracle_candidate_dependencies_readonly.py"
spec = importlib.util.spec_from_file_location("oracle_dependency_preflight", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

BASE = b"""import hmac
from fastapi import Header, HTTPException
pairing_key = "dummy"
def create_app():
    @app.get("/v2/snapshot")
    def snapshot():
        return object()
"""


class DependencyPreflightTests(unittest.TestCase):
    def test_static_bindings_and_sha_required(self):
        with patch.object(module, "EXPECTED_SHA", hashlib.sha256(BASE).hexdigest()):
            result = module.inspect_source(BASE)
        self.assertTrue(result["static_pass"])
        self.assertTrue(all(result["bindings"].values()))

    def test_missing_binding_holds(self):
        raw = BASE.replace(b"import hmac\n", b"")
        with patch.object(module, "EXPECTED_SHA", hashlib.sha256(raw).hexdigest()):
            result = module.inspect_source(raw)
        self.assertFalse(result["static_pass"])
        self.assertFalse(result["bindings"]["hmac"])

    def test_wrong_sha_holds(self):
        self.assertFalse(module.inspect_source(BASE)["static_pass"])

    def test_late_binding_holds(self):
        raw = BASE.replace(b'pairing_key = "dummy"\n', b"") + b'pairing_key = "late"\n'
        with patch.object(module, "EXPECTED_SHA", hashlib.sha256(raw).hexdigest()):
            result = module.inspect_source(raw)
        self.assertFalse(result["static_pass"])
        self.assertFalse(result["bindings"]["pairing_key"])

    def test_wrong_factory_holds(self):
        raw = BASE.replace(b"def create_app():", b"def other():")
        with patch.object(module, "EXPECTED_SHA", hashlib.sha256(raw).hexdigest()):
            result = module.inspect_source(raw)
        self.assertFalse(result["static_pass"])
        self.assertFalse(result["factory_found"])


if __name__ == "__main__":
    unittest.main()
