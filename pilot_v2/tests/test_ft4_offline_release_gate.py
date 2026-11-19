"""Move 3/4 offline-only acceptance: bundle completeness and release gates.

This cannot claim Oracle deployment, Android binary signing, or live data.
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from pilot_v2.android_build_gate import inspect

REPO = Path(__file__).resolve().parents[2]


class ReleasePreflightTests(unittest.TestCase):
    def test_actual_v2_identity_preflight_never_approves_release(self):
        result = inspect(REPO)
        self.assertEqual(result["status"], "PASS", result["failures"])
        self.assertEqual(result["target_package"], "com.botking.bot_king_v2")
        for key in ("apk_generated", "apk_identity_verified", "signing_verified",
                    "release_ready", "production_deployment_approved"):
            self.assertFalse(result[key])
        self.assertGreater(len(result["release_blockers"]), 0)

    def test_identity_mismatch_and_premature_release_switch_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for relative in (
                "pyproject.toml",
                "pilot_v2/pilot_identity.json",
                "pilot_v2/android_app/pyproject.toml",
                "pilot_v2/android_app/src/main.py",
                "pilot_v2/android_app/src/app_identity.py",
            ):
                dest = root / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(REPO / relative, dest)
            metadata_path = root / "pilot_v2/pilot_identity.json"
            metadata = json.loads(metadata_path.read_text())
            metadata["apk_build_enabled"] = True
            metadata["version_name"] = "2.0.101"
            metadata_path.write_text(json.dumps(metadata))
            result = inspect(root)
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("Pilot release gates must remain OFF", result["failures"])
            self.assertIn("V2 version mismatch", result["failures"])
            self.assertFalse(result["release_ready"])
            self.assertFalse(result["production_deployment_approved"])


if __name__ == "__main__":
    unittest.main()
