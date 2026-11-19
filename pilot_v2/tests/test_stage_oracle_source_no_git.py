"""Offline tests for pinned no-git V2 Oracle staging."""
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "stage_oracle_source_no_git.py"
spec = importlib.util.spec_from_file_location("stage_v2_oracle", SCRIPT)
stage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage)
SHA = "a" * 40


def archive(missing=None, extra=None):
    buf = io.BytesIO()
    required = ("http_gateway.py", "api_contract.py", "device_sessions.py",
                "durable_device_sessions.py", "verified_login_gateway.py",
                "durable_challenges.py", "atomic_verified_login.py",
                "unified_gateway_app.py", "unified_data_pipeline.py", "internal_dhan_read_port.py", "shared_read_budget.py", "trusted_http_adapter.py", "private_backup_vault.py", "isolated_gateway_app.py")
    with zipfile.ZipFile(buf, "w") as z:
        for n in required:
            if n != missing:
                z.writestr(f"owner-repo-{SHA[:7]}/pilot_v2/{n}", f"# {n}\n")
        if extra:
            z.writestr(f"owner-repo-{SHA[:7]}/pilot_v2/{extra}", "untrusted\n")
        z.writestr(f"owner-repo-{SHA[:7]}/server.py", "V1 BLOCKED")
    return buf.getvalue()


class NoGitStageTests(unittest.TestCase):
    def test_stages_only_v2_source_and_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            dst = Path(d) / "source"
            result = stage.unpack(archive(), dst, SHA)
            self.assertEqual(result["commit"], SHA)
            self.assertFalse(result["production_ready"])
            self.assertFalse(result["oracle_deployed"])
            self.assertFalse((dst / "server.py").exists())
            self.assertTrue((dst / "pilot_v2/http_gateway.py").is_file())

    def test_missing_unified_gateway_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            dst = Path(d) / "source"
            with self.assertRaises(ValueError):
                stage.unpack(archive(missing="unified_gateway_app.py"), dst, SHA)
            self.assertFalse(dst.exists())

    def test_missing_module_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            dst = Path(d) / "source"
            with self.assertRaises(ValueError):
                stage.unpack(archive(missing="http_gateway.py"), dst, SHA)
            self.assertFalse(dst.exists())

    def test_existing_destination_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            dst = Path(d) / "source"
            dst.mkdir()
            sentinel = dst / "keep"
            sentinel.write_text("SAFE")
            with self.assertRaises(FileExistsError):
                stage.unpack(archive(), dst, SHA)
            self.assertEqual(sentinel.read_text(), "SAFE")

    def test_rejects_bad_commit(self):
        with self.assertRaises(ValueError):
            stage.validate_commit("main")

    def test_does_not_extract_nested_scripts(self):
        with tempfile.TemporaryDirectory() as d:
            dst = Path(d) / "source"
            stage.unpack(archive(extra="nested.py"), dst, SHA)
            self.assertFalse((dst / "server.py").exists())


if __name__ == "__main__":
    unittest.main()
