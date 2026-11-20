"""Source guard: V2 pilot APK workflow must never touch V1 or claim LIVE."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/botking-v2-android-pilot.yml"


class V2AndroidPilotBuildContractTests(unittest.TestCase):
    def test_standalone_build_is_pinned_and_separate(self):
        text = WORKFLOW.read_text()
        for required in ("botking-v2-android-pilot.yml", "bot_king_v2",
                         "com.botking", "com.botking.bot_king_v2",
                         "versionCode='100'", "versionName='2\\.0\\.100'",
                         "flet==0.25.2", "flet-cli==0.25.2",
                         "python -m unittest discover", "apksigner",
                         "aapt", "upload-artifact@v4",
                         "bot-king-v2-offline-pilot-apk-2.0.100"):
            self.assertIn(required, text)
        for banned in ("systemctl restart", "systemctl stop", "sudo systemctl",
                       "/opt/bot-king-server", "live_orders_enabled = true",
                       "actions/checkout@v3"):
            self.assertNotIn(banned, text)

    def test_ephemeral_signer_is_explicitly_nonproduction_and_not_uploaded(self):
        text = WORKFLOW.read_text()
        self.assertIn("NONPRODUCTION TEST", text)
        self.assertIn("Reinstall needed", text)
        self.assertIn("sha256sum", text)
        self.assertIn("Remove temporary pilot signer", text)
        self.assertIn("retention-days: 7", text)
        self.assertNotIn("path: $RUNNER_TEMP/botking-v2-only", text)
