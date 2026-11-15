"""Protect final BOT KING branch's release/build workflow contract."""
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]

class ReleaseBranchParity(unittest.TestCase):
    def test_joint_branch_is_eligible_for_version_push_build(self):
        workflow=(ROOT/".github/workflows/build.yml").read_text()
        self.assertIn("fix/botking-joint-audit-70-15-20261115",workflow)
        self.assertIn("      - pyproject.toml",workflow)
        self.assertIn("workflow_dispatch:",workflow)

    def test_signed_release_and_version_increment_checks_remain(self):
        workflow=(ROOT/".github/workflows/build.yml").read_text()
        for check in ("Permanent release signing", "BOTKING_SIGNING_SHA256",
                      "--build-number", "versionCode", "versionName",
                      "apksigner", "Verify single-source release version"):
            self.assertIn(check,workflow)

if __name__=="__main__":
    unittest.main()
