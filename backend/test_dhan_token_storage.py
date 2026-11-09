"""Offline tests for isolated token storage; no real credentials or Oracle writes."""
import os
from pathlib import Path
from unittest.mock import patch
import stat
import tempfile
import unittest

from dhan_token_storage import atomic_store_token, read_persisted_token


class TokenStorageTests(unittest.TestCase):
    def test_atomic_replacement_and_permissions(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "dhan-token"
            target.write_text("OLD_FAKE_TOKEN\n")
            os.chmod(target, 0o600)
            atomic_store_token(target, "NEW_FAKE_TOKEN")
            self.assertEqual(target.read_text(), "NEW_FAKE_TOKEN\n")
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)
            self.assertEqual(list(Path(folder).glob(".dhan-token-*")), [])

    def test_oversized_token_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "dhan-token"
            atomic_store_token(target, "OLD_FAKE_TOKEN")
            with self.assertRaises(ValueError):
                atomic_store_token(target, "X" * 8192)
            self.assertEqual(read_persisted_token(target), "OLD_FAKE_TOKEN")

    def test_restart_roundtrip_from_disk(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "dhan-token"
            atomic_store_token(target, "FAKE_SESSION_TOKEN")
            self.assertEqual(read_persisted_token(target), "FAKE_SESSION_TOKEN")

    def test_reader_rejects_insecure_permissions(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "dhan-token"
            target.write_text("FAKE_TOKEN")
            os.chmod(target, 0o644)
            with self.assertRaises(PermissionError):
                read_persisted_token(target)

    def test_reader_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "token"
            atomic_store_token(target, "FAKE_TOKEN")
            link = Path(folder) / "link"
            link.symlink_to(target)
            with self.assertRaises(OSError):
                read_persisted_token(link)

    def test_reject_invalid_tokens_without_touching_existing(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "dhan-token"
            target.write_text("ORIGINAL\n")
            os.chmod(target, 0o600)
            for token in ("", " leading", "trailing ", "two\nlines", None):
                with self.subTest(token=repr(token)):
                    with self.assertRaises(ValueError):
                        atomic_store_token(target, token)
                    self.assertEqual(target.read_text(), "ORIGINAL\n")

    def test_existing_token_wrong_owner_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "dhan-token"
            atomic_store_token(target, "OLD_FAKE_TOKEN")
            with patch("dhan_token_storage.os.geteuid", return_value=-1):
                with self.assertRaises(PermissionError):
                    atomic_store_token(target, "NEW_FAKE_TOKEN")
            self.assertEqual(read_persisted_token(target), "OLD_FAKE_TOKEN")

    def test_existing_token_insecure_mode_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "dhan-token"
            atomic_store_token(target, "OLD_FAKE_TOKEN")
            os.chmod(target, 0o644)
            with self.assertRaises(PermissionError):
                atomic_store_token(target, "NEW_FAKE_TOKEN")
            self.assertEqual(target.read_text(), "OLD_FAKE_TOKEN\n")

    def test_reject_symlink_target(self):
        with tempfile.TemporaryDirectory() as folder:
            real = Path(folder) / "real"
            real.write_text("UNCHANGED")
            link = Path(folder) / "dhan-token"
            link.symlink_to(real)
            with self.assertRaises(ValueError):
                atomic_store_token(link, "NEW_FAKE_TOKEN")
            self.assertEqual(real.read_text(), "UNCHANGED")

    def test_reject_world_writable_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder) / "unsafe"
            directory.mkdir()
            os.chmod(directory, 0o777)
            with self.assertRaises(PermissionError):
                atomic_store_token(directory / "dhan-token", "FAKE_TOKEN")


if __name__ == "__main__":
    unittest.main()
