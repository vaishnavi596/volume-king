import hashlib
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from pilot_v2.tools.remote_stage_archive import stage, REQUIRED


def bundle(extra=None):
    files = {name: b"VALUE = 1\n" for name in REQUIRED}
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
            with patch("pathlib.Path.home", return_value=home):
                with self.assertRaises(FileExistsError):
                    stage(archive, sha="a" * 40, checksum=result["archive_sha256"], root=root)

    def test_valid(self):
        self.run_stage(bundle())

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
