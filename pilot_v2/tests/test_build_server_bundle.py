"""Offline source bundle safety tests. No Oracle, provider or network activity."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "build_server_bundle.py"
spec = importlib.util.spec_from_file_location("v2_bundle_builder", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class BundleTests(unittest.TestCase):
    def make_sources(self, root):
        base = root / "pilot_v2"
        base.mkdir()
        for name in module.REQUIRED:
            (base / name).write_text("# isolated test fixture\n", encoding="utf8")
        return base

    def test_manifest_is_fail_closed_and_hash_verified(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = self.make_sources(root)
            target = root / "stage.zip"
            manifest = module.build(target, src)
            self.assertFalse(manifest["production_ready"])
            self.assertFalse(manifest["enabled"])
            self.assertFalse(manifest["oracle_deployed"])
            with ZipFile(target) as bundle:
                self.assertEqual(set(bundle.namelist()), {
                    "manifest.json",
                    *("pilot_v2/" + name for name in module.REQUIRED),
                })
                self.assertEqual(json.loads(bundle.read("manifest.json")), manifest)
                self.assertTrue(all(
                    bundle.read("pilot_v2/" + n) == (src / n).read_bytes()
                    for n in module.REQUIRED
                ))

    def test_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = self.make_sources(root)
            dst = root / "existing.zip"
            dst.write_bytes(b"KEEP")
            with self.assertRaises(FileExistsError):
                module.build(dst, src)
            self.assertEqual(dst.read_bytes(), b"KEEP")

    def test_complete_gateway_source_is_mandatory(self):
        self.assertIn("unified_gateway_app.py", module.REQUIRED)
        self.assertIn("private_backup_vault.py", module.REQUIRED)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = self.make_sources(root)
            (source / "private_backup_vault.py").unlink()
            with self.assertRaises(FileNotFoundError):
                module.build(root / "missing.zip", source)
            self.assertFalse((root / "missing.zip").exists())

    def test_rejects_missing_source(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = self.make_sources(root)
            (src / module.REQUIRED[0]).unlink()
            with self.assertRaises(FileNotFoundError):
                module.build(root / "stage.zip", src)

    def test_rejects_non_v2_root(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "wrong_root"
            root.mkdir()
            with self.assertRaises(ValueError):
                module.build(root / "stage.zip", root)


if __name__ == "__main__":
    unittest.main()
