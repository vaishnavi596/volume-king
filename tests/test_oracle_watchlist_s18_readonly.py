"""Offline checks for S18 read-only source auditor; no Oracle access."""
import tempfile
import unittest
from pathlib import Path

from scripts.audit_oracle_watchlist_s18_readonly import audit
from scripts.oracle_s18_watchlist_patch import make_stage
from tests.test_oracle_s18_watchlist_patch import FIXTURE


class S18ReadOnlyAuditTests(unittest.TestCase):
    def check(self, source):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "watchlist_store.py"
            path.write_text(source, encoding="utf-8")
            return audit(path)

    def test_unpatched_fixture_is_not_misclassified(self):
        data = self.check(FIXTURE)
        self.assertEqual(data["syntax"], "PASS")
        self.assertFalse(data["cross_list_duplicate_source_signature"])
        self.assertFalse(data["global_70_source_signature"])
        self.assertFalse(data["runtime_enforcement_verified"])
        self.assertFalse(data["production_changed"])

    def test_staged_patch_has_expected_signatures_but_not_runtime_proof(self):
        data = self.check(make_stage(FIXTURE))
        self.assertTrue(data["cross_list_duplicate_source_signature"])
        self.assertTrue(data["global_70_source_signature"])
        self.assertFalse(data["runtime_enforcement_verified"])
        self.assertFalse(data["saved_watchlists_inspected"])
        self.assertEqual(data["dhan_requests_made"], 0)

    def test_comments_only_do_not_fake_source_signatures(self):
        source = FIXTURE + "\n# Symbol already belongs to another watchlist\n# Global limit: 70 symbols across all watchlists\n"
        data = self.check(source)
        self.assertFalse(data["cross_list_duplicate_source_signature"])
        self.assertFalse(data["global_70_source_signature"])

    def test_partial_guard_not_reported_complete(self):
        patched = make_stage(FIXTURE).replace(
            '"Global limit: 70 symbols across all watchlists"',
            '"Invalid maximum"')
        data = self.check(patched)
        self.assertTrue(data["cross_list_duplicate_source_signature"])
        self.assertFalse(data["global_70_source_signature"])

    def test_missing_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "regular non-symlink"):
                audit(Path(directory) / "missing.py")


if __name__ == "__main__":
    unittest.main()
