"""Static release gates for manual or version-bump BOT KING APK workflow."""
from pathlib import Path
import re
import tomllib
import unittest

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=(ROOT/".github/workflows/build.yml").read_text(encoding="utf-8")
PROJECT=tomllib.loads((ROOT/"pyproject.toml").read_text(encoding="utf-8"))
SOURCE=(ROOT/"src/main.py").read_text(encoding="utf-8")

class AndroidReleaseWorkflowGuards(unittest.TestCase):
    def test_apk_requires_manual_dispatch_or_release_branch_version_bump(self):
        self.assertRegex(WORKFLOW,r"(?m)^on:\s*\n\s*workflow_dispatch:")
        self.assertRegex(WORKFLOW,r"(?m)^\s+push:\s*\n\s+branches:\s*\[[^\]\n]+\]\s*\n\s+paths:\s*\n\s+- pyproject\.toml")
        self.assertIn("fix/botking-2399-candle-retry-20261114", WORKFLOW)

    def test_release_version_is_synchronized(self):
        version=PROJECT["project"]["version"]
        self.assertRegex(version,r"^\d+\.\d+\.\d+$")
        # The runtime version comes from package metadata, or the same project
        # file when running from source. No second literal version to drift.
        self.assertIn('APP_VERSION = package_version("bot-king")', SOURCE)
        self.assertIn('tomllib.loads(_project_file.read_text(encoding="utf-8"))["project"]["version"]', SOURCE)
        self.assertNotRegex(SOURCE,r'APP_VERSION\s*=\s*"\d+\.\d+\.\d+"')

    def test_release_signing_fails_closed(self):
        for name in ("BOTKING_KEYSTORE_BASE64","BOTKING_KEYSTORE_PASSWORD",
                     "BOTKING_KEY_PASSWORD","BOTKING_KEY_ALIAS","BOTKING_SIGNING_SHA256"):
            self.assertIn(name,WORKFLOW)
        self.assertIn('ACTUAL" != "$EXPECTED"',WORKFLOW)
        self.assertIn("exit 1",WORKFLOW)

    def test_build_number_advances_by_workflow_run(self):
        self.assertIn('GITHUB_RUN_NUMBER * 100 + GITHUB_RUN_ATTEMPT',WORKFLOW)
        self.assertIn('--build-number "$BUILD_CODE"',WORKFLOW)

    def test_offline_regression_runs_before_packaging(self):
        self.assertLess(WORKFLOW.index("python -m unittest discover -s tests"),
                        WORKFLOW.index("flet build apk"))

if __name__=="__main__":
    unittest.main()
