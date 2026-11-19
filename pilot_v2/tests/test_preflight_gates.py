"""Offline Oracle preflight and V2 APK identity gate tests (no host changes)."""
import pathlib
import tempfile
import unittest
import json
from unittest.mock import patch
from types import SimpleNamespace
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
    def test_bounded_dual_service_metadata_never_reads_secret_environment(self):
        commands = []
        def fake_run(argv, **kwargs):
            commands.append(argv)
            self.assertNotIn("Environment", " ".join(argv))
            name = argv[2]
            path = "/opt/bot-king-server" if name == "bot-king.service" else "/opt/bot-king-v2"
            return SimpleNamespace(returncode=0, stdout=(
                "ActiveState=active\\nWorkingDirectory=" + path +
                "\\nEnvironment=SECRET_SHOULD_NEVER_BE_REPORTED\\n"))
        with tempfile.TemporaryDirectory() as d, patch(
                "pilot_v2.oracle_preflight.subprocess.run",
                side_effect=fake_run):
            result = audit_local(d, include_v2_service=True)
            self.assertEqual(len(commands), 2)
            self.assertEqual(commands[0][2], "bot-king.service")
            self.assertEqual(commands[1][2], "bot-king-v2.service")
            self.assertTrue(result["v2_isolated_workdir"])
            self.assertNotIn("SECRET_SHOULD_NEVER_BE_REPORTED", json.dumps(result))
            self.assertEqual(result["source_files"]["server.py"]["present"], False)
            self.assertEqual(result["orders_sent"], 0)

    def test_v2_service_missing_cannot_claim_workdir_isolation(self):
        def fake_run(argv, **kwargs):
            if argv[2] == "bot-king-v2.service":
                return SimpleNamespace(returncode=1, stdout="")
            return SimpleNamespace(returncode=0,
                                   stdout="WorkingDirectory=/opt/bot-king-server\\n")
        with tempfile.TemporaryDirectory() as d, patch(
                "pilot_v2.oracle_preflight.subprocess.run",
                side_effect=fake_run):
            result = audit_local(d, include_v2_service=True)
            self.assertFalse(result["v2_isolated_workdir"])
            self.assertEqual(result["v2_service"]["status"], "UNAVAILABLE")
            self.assertFalse(result["production_changed"])

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
        self.assertEqual(result["version"],"2.0.100")
        self.assertEqual(result["version_code"],100)
    def test_future_coordinated_v2_version_increment_allowed_without_release(self):
        original=pathlib.Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            copies=("pilot_v2/pilot_identity.json",
                    "pilot_v2/android_app/pyproject.toml",
                    "pilot_v2/android_app/src/main.py",
                    "pilot_v2/android_app/src/app_identity.py",
                    "pyproject.toml")
            for relative in copies:
                target=root/relative
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes((original/relative).read_bytes())
            metadata=root/"pilot_v2/pilot_identity.json"
            app=root/"pilot_v2/android_app/src/app_identity.py"
            pyproject=root/"pilot_v2/android_app/pyproject.toml"
            record=json.loads(metadata.read_text())
            for version in (101,102,125):
                record["version_name"]=f"2.0.{version}"
                record["version_code"]=version
                metadata.write_text(json.dumps(record))
                app.write_text((original/"pilot_v2/android_app/src/app_identity.py")
                               .read_text().replace("2.0.100",f"2.0.{version}")
                               .replace("APP_VERSION_CODE = 100",
                                        f"APP_VERSION_CODE = {version}"))
                pyproject.write_text((original/"pilot_v2/android_app/pyproject.toml")
                                     .read_text().replace("2.0.100",f"2.0.{version}"))
                result=inspect(root)
                self.assertEqual(result["status"],"PASS", result["failures"])
                self.assertFalse(result["release_ready"])
                self.assertFalse(result["apk_generated"])
                self.assertFalse(result["production_deployment_approved"])
            # A mismatched or downgraded version is never accepted.
            record["version_name"]="2.0.101"
            record["version_code"]=100
            metadata.write_text(json.dumps(record))
            self.assertEqual(inspect(root)["status"],"FAIL")
            record["version_name"]="2.0.099"
            record["version_code"]=99
            metadata.write_text(json.dumps(record))
            self.assertEqual(inspect(root)["status"],"FAIL")
            record["version_name"]="2.0.101"
            record["version_code"]=True
            metadata.write_text(json.dumps(record))
            self.assertEqual(inspect(root)["status"],"FAIL")

    def test_displayed_app_version_mismatch_blocks_static_preflight(self):
        original=pathlib.Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            copies=("pilot_v2/pilot_identity.json",
                    "pilot_v2/android_app/pyproject.toml",
                    "pilot_v2/android_app/src/main.py",
                    "pilot_v2/android_app/src/app_identity.py",
                    "pyproject.toml")
            for relative in copies:
                target=root/relative
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes((original/relative).read_bytes())
            self.assertEqual(inspect(root)["status"],"PASS")
            path=root/"pilot_v2/android_app/src/app_identity.py"
            path.write_text(path.read_text().replace(
                'APP_VERSION_CODE = 100','APP_VERSION_CODE = 101'))
            broken=inspect(root)
            self.assertEqual(broken["status"],"FAIL")
            self.assertFalse(broken["release_ready"])
            self.assertIn("Displayed app version/package mismatches V2 identity",
                          broken["failures"])
            path.write_text('APP_VERSION_NAME = "2.0.100"\\n'
                            'APP_VERSION_CODE = True\\n'
                            'APP_PACKAGE = "com.botking.bot_king_v2"\\n')
            self.assertEqual(inspect(root)["status"],"FAIL")

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
