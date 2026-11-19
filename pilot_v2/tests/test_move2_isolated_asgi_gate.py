"""Static contract coverage for isolated Move-2 ASGI gate, no pip/Oracle calls."""
import importlib.util
from pathlib import Path
import tempfile
import json
import hashlib
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "move2_isolated_asgi_gate.py"
spec = importlib.util.spec_from_file_location("v2_move2_gate", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Move2GateTests(unittest.TestCase):
    def test_v2_stage_manifest_verified(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            stage = base / "source"
            module = stage / "pilot_v2" / "isolated_gateway_app.py"
            module.parent.mkdir(parents=True)
            module.write_text("# offline stage only", encoding="utf-8")
            digest = hashlib.sha256(module.read_bytes()).hexdigest()
            (stage / "manifest.json").write_text(json.dumps({
                "commit": "a" * 40, "source_only": True,
                "enabled": False, "production_ready": False, "oracle_deployed": False,
                "files": {"isolated_gateway_app.py": digest}
            }))
            self.assertEqual(m.verify_source(stage)["commit"], "a" * 40)
            module.write_text("# tampered", encoding="utf-8")
            with self.assertRaises(ValueError):
                m.verify_source(stage)

    def test_requires_fail_closed_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            stage = Path(d)
            (stage / "manifest.json").write_text(json.dumps({
                "source_only": False, "enabled": True,
                "production_ready": True, "oracle_deployed": True, "files": {}
            }))
            with self.assertRaises(ValueError):
                m.verify_source(stage)

    def test_only_isolated_workspace(self):
        base = Path("/tmp/private-v2-isolated")
        self.assertTrue(m.inside(base, base / "stage"))
        self.assertFalse(m.inside(base, Path("/opt/bot-king-server")))

    def test_dependency_set_has_no_dhan_or_order_package(self):
        self.assertIn("fastapi==0.115.12", m.DEPS)
        self.assertIn("httpx==0.28.1", m.DEPS)
        self.assertEqual(len(m.DEPS), 2)


if __name__ == "__main__":
    unittest.main()
