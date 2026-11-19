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

    def test_staged_source_verifier_checks_hash_and_never_activates(self):
        with tempfile.TemporaryDirectory() as d:
            dst = Path(d) / "source"
            stage.unpack(archive(), dst, SHA)
            result = stage.verify_staged_source(dst, SHA)
            self.assertEqual(result["integrity"], "MATCHED_LOCAL_MANIFEST")
            self.assertFalse(result["production_ready"])
            self.assertFalse(result["activated"])
            source = dst / "pilot_v2" / "http_gateway.py"
            source.write_text("TAMPER")
            with self.assertRaises(ValueError):
                stage.verify_staged_source(dst, SHA)

    def test_staging_audit_refuses_extra_symlink_and_false_enablement(self):
        with tempfile.TemporaryDirectory() as d:
            dst = Path(d) / "source"
            stage.unpack(archive(), dst, SHA)
            extra = dst / "pilot_v2" / "unexpected.py"
            extra.write_text("unsafe")
            with self.assertRaises(ValueError):
                stage.verify_staged_source(dst, SHA)
            extra.unlink()
            manifest = dst / "manifest.json"
            import json
            data = json.loads(manifest.read_text())
            data["enabled"] = True
            manifest.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                stage.verify_staged_source(dst, SHA)

    def test_manifest_and_files_cannot_jointly_hide_required_source(self):
        with tempfile.TemporaryDirectory() as d:
            dst = Path(d) / "source"
            stage.unpack(archive(), dst, SHA)
            missing = "unified_gateway_app.py"
            (dst / "pilot_v2" / missing).unlink()
            manifest = dst / "manifest.json"
            import json
            content = json.loads(manifest.read_text())
            content["files"].pop(missing)
            manifest.write_text(json.dumps(content))
            with self.assertRaises(ValueError):
                stage.verify_staged_source(dst, SHA)

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
