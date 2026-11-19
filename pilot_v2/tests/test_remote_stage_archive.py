import hashlib
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from pilot_v2.tools.remote_stage_archive import stage, REQUIRED, REQUIRED_TOOLS


def bundle(extra=None, *, omit=frozenset()):
    files = {name: b"VALUE = 1\n" for name in (REQUIRED | REQUIRED_TOOLS) - set(omit)}
    files.update(extra or {})
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for name, data in sorted(files.items()):
            item = tarfile.TarInfo(name)
            item.size = len(data)
            tf.addfile(item, io.BytesIO(data))
    return buf.getvalue()


class StageTests(unittest.TestCase):
    def run_stage(self, data, checksum=None):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            root = home / "botking-v2-staging"
            archive = home / "source.tgz"
            archive.write_bytes(data)
            with patch("pathlib.Path.home", return_value=home):
                result = stage(archive, sha="a" * 40,
                    checksum=checksum or hashlib.sha256(data).hexdigest(), root=root)
            self.assertFalse(result["activated"])
            self.assertTrue((root / ("gh-" + "a" * 40) / "pilot_v2" / "unified_gateway_app.py").is_file())
            self.assertTrue((root / ("gh-" + "a" * 40) / "pilot_v2" / "tools" / "v2_activation_gate.py").is_file())
            with patch("pathlib.Path.home", return_value=home):
                with self.assertRaises(FileExistsError):
                    stage(archive, sha="a" * 40, checksum=result["archive_sha256"], root=root)

    def test_workflow_archive_includes_nonactivating_owner_security_tools(self):
        workflow = (Path(__file__).resolve().parents[2] / ".github" /
                    "workflows" / "v2-oracle-source-stage.yml").read_text()
        marker = "tar -czf /tmp/botking-v2-source.tgz"
        self.assertIn(marker, workflow)
        actual = workflow[workflow.index(marker):workflow.index("HASH=", workflow.index(marker))]
        self.assertIn("tools/v2_activation_gate.py", actual)
        self.assertIn("tools/provision_oracle_master.py", actual)
        self.assertIn("$(cd pilot_v2 && ls *.py)", actual)
        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("systemctl restart", workflow)
        self.assertNotIn("on:\n  push:", workflow)

    def test_valid(self):
        self.run_stage(bundle())

    def test_missing_security_tool_denied(self):
        # Staged bundle without activation controls must fail closed.
        for name in REQUIRED_TOOLS:
            self._expect_bundle_rejected(bundle(omit={name}))

    def _expect_bundle_rejected(self, data, missing=None):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            archive = home / "source.tgz"
            archive.write_bytes(data)
            with patch("pathlib.Path.home", return_value=home):
                with self.assertRaises(ValueError):
                    stage(archive, sha="a" * 40,
                          checksum=hashlib.sha256(data).hexdigest(), root=home / "botking-v2-staging")

    def test_nested_path_traversal_denied(self):
        self._expect_bundle_rejected(bundle({"tools/../unsafe.py": b"VALUE = 1\n"}))

    def test_wrong_hash(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            archive = home / "source.tgz"
            archive.write_bytes(bundle())
            with patch("pathlib.Path.home", return_value=home):
                with self.assertRaises(ValueError):
                    stage(archive, sha="a" * 40, checksum="0" * 64,
                          root=home / "botking-v2-staging")

    def test_missing_module(self):
        bad = bundle()
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            archive = home / "source.tgz"
            archive.write_bytes(bad)
            with patch("pathlib.Path.home", return_value=home):
                with self.assertRaises(ValueError):
                    stage(archive, sha="a" * 40,
                          checksum=hashlib.sha256(bad).hexdigest(), root=home / "wrong-root")

    def test_path_traversal_rejected(self):
        data = bundle({"../bad.py": b"VALUE = 2\n"})
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            archive = home / "source.tgz"
            archive.write_bytes(data)
            with patch("pathlib.Path.home", return_value=home):
                with self.assertRaises(ValueError):
                    stage(archive, sha="a" * 40,
                          checksum=hashlib.sha256(data).hexdigest(), root=home / "botking-v2-staging")


if __name__ == "__main__":
    unittest.main()
