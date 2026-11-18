"""Offline Oracle preflight and V2 APK identity gate tests (no host changes)."""
import pathlib
import tempfile
import unittest
import json
from pilot_v2.oracle_preflight import audit_local
from pilot_v2.android_build_gate import inspect

class PreflightTests(unittest.TestCase):
    def test_oracle_source_hashes_without_reading_env(self):
        with tempfile.TemporaryDirectory() as d:
            path=pathlib.Path(d)
            (path/"server.py").write_text("synthetic server")
            (path/"server.env").write_text("SECRET_TOKEN=never_print")
            result=audit_local(path,include_systemd=False)
            self.assertEqual(result["status"],"READ_ONLY")
            self.assertTrue(result["source_files"]["server.py"]["present"])
            self.assertFalse(result["source_files"]["dhan_feed.py"]["present"])
            self.assertFalse(result["production_changed"])
            self.assertEqual(result["dhan_requests"],0)
            self.assertNotIn("SECRET_TOKEN",json.dumps(result))
            self.assertNotIn("never_print",json.dumps(result))
    def test_android_v2_identity_gate_without_build(self):
        root=pathlib.Path(__file__).resolve().parents[2]
        result=inspect(root)
        self.assertEqual(result["status"],"PASS")
        self.assertFalse(result["apk_generated"])
        self.assertFalse(result["apk_identity_verified"])
        self.assertFalse(result["signing_verified"])
        self.assertFalse(result["release_ready"])
        self.assertFalse(result["production_deployment_approved"])
        self.assertGreaterEqual(len(result["release_blockers"]), 4)
        self.assertTrue(any("APK" in item for item in result["release_blockers"]))
        self.assertTrue(any("Login" in item for item in result["release_blockers"]))
        self.assertNotEqual(result["target_package"],"com.botking.bot_king")
    def test_mutated_metadata_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            (root/"pilot_v2/android_app/src").mkdir(parents=True)
            (root/"pilot_v2/android_app/src/main.py").write_text("pass")
            (root/"pilot_v2/pilot_identity.json").write_text(json.dumps({
                "version_name":"2.0.100","version_code":100,
                "android_package":"com.botking.bot_king",
                "legacy_package":"com.botking.bot_king","gateway_enabled":False,
                "apk_build_enabled":False,"live_orders_enabled":False}))
            (root/"pilot_v2/android_app/pyproject.toml").write_text(
                '[project]\nname="v2"\nversion="2.0.100"\n')
            (root/"pyproject.toml").write_text('[project]\nname="old"\n')
            failure = inspect(root)
            self.assertEqual(failure["status"],"FAIL")
            self.assertFalse(failure["release_ready"])
            self.assertFalse(failure["production_deployment_approved"])
if __name__=="__main__":
    unittest.main()
