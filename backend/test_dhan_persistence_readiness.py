"""Offline filesystem readiness tests; no production paths or credentials."""
import os
from pathlib import Path
import tempfile
import unittest

from check_dhan_persistence_readiness import check_storage_readiness


class PersistenceReadinessTests(unittest.TestCase):
    def test_private_directory_and_owned_token_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "token"
            target.write_text("FAKE_TOKEN\n")
            os.chmod(target, 0o600)
            self.assertEqual(check_storage_readiness(target), [])

    def test_other_owner_detected_without_reading_token(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "token"
            target.write_text("FAKE_TOKEN\n")
            os.chmod(target, 0o600)
            self.assertIn("token_file_owned_by_other_user", check_storage_readiness(target, uid=-1))

    def test_insecure_file_mode_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "token"
            target.write_text("FAKE_TOKEN\n")
            os.chmod(target, 0o640)
            self.assertIn("token_file_permissions_not_0600", check_storage_readiness(target))

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "token"
            target.symlink_to(Path(folder) / "other")
            self.assertIn("token_path_symlink", check_storage_readiness(target))

    def test_group_writable_parent_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            os.chmod(folder, 0o770)
            target = Path(folder) / "token"
            self.assertIn("credential_directory_writable_by_others", check_storage_readiness(target))


if __name__ == "__main__":
    unittest.main()
