"""Pure offline route audit regression: no secrets, network or Oracle writes."""
import ast
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_oracle_app_routes_readonly.py"


def load_audit():
    spec = importlib.util.spec_from_file_location("oracle_route_audit", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OracleReadOnlyRouteAudit(unittest.TestCase):
    def test_script_is_python_syntax_safe(self):
        ast.parse(SCRIPT.read_text(encoding="utf-8"))

    def test_actual_github_server_defines_all_nine_app_routes(self):
        a = load_audit()
        result = a.audit(ROOT / "backend" / "server.py")
        self.assertEqual(result["expected_routes"], 9)
        self.assertEqual(result["source_present"], 9)
        self.assertEqual(result["source_missing"], [])
        self.assertFalse(result["runtime_routes_verified"])
        self.assertFalse(result["collector_enabled_verified"])
        self.assertFalse(result["protected_quotes_verified"])
        self.assertFalse(result["production_changed"])

    def test_missing_route_remains_missing_instead_of_faked(self):
        a = load_audit()
        source = ('def create_app():\n'
                  '    @app.get("/v2/snapshot")\n'
                  '    def view():\n'
                  '        return {}\n')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "server.py"
            path.write_text(source, encoding="utf-8")
            result = a.audit(path)
        self.assertEqual(result["source_present"], 1)
        self.assertEqual(len(result["source_missing"]), 8)

    def test_symlink_rejected_before_inspection(self):
        a = load_audit()
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "source.py"
            target.write_text("pass\n", encoding="utf-8")
            link = Path(tmp) / "server.py"
            link.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "non-symlink"):
                a.audit(link)


if __name__ == "__main__":
    unittest.main()
