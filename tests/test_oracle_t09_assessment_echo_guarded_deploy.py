"""Offline only: guarded T09 deployment must fail closed and roll back."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = (Path(__file__).resolve().parents[1] / "scripts"
          / "deploy_oracle_t09_assessment_echo_guarded_20261118.py")
spec = importlib.util.spec_from_file_location("t09_guarded_deploy", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class T09AssessmentEchoDeployTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        p = Path(self.t.name)
        self.root, self.backup = p / "prod", p / "backup"
        self.root.mkdir()
        self.backup.mkdir()
        self.candidate = p / "candidate.py"
        self.raw = {}
        for name in ("server.py", "assessment_state.py", "assessment_api.py"):
            raw = ("# existing " + name + "\npass\n").encode()
            self.raw[name] = raw
            (self.root/name).write_bytes(raw)
            (self.backup/name).write_bytes(raw)
        self.candidate_raw = b"# T09 echo\npass\n"
        self.candidate.write_bytes(self.candidate_raw)
        self.old = (mod.ROOT, mod.BACKUP, mod.CANDIDATE, mod.TARGET,
                    mod.ORIGINAL, mod.CANDIDATE_SHA, mod.REPORT.copy(), mod.mutated)
        mod.ROOT, mod.BACKUP = self.root, self.backup
        mod.CANDIDATE, mod.TARGET = self.candidate, self.root/"assessment_api.py"
        mod.ORIGINAL = {n: hashlib.sha256(data).hexdigest() for n,data in self.raw.items()}
        mod.CANDIDATE_SHA = hashlib.sha256(self.candidate_raw).hexdigest()
        mod.REPORT = {"production_changed": False, "server_restarted": False}
        mod.mutated = False

    def tearDown(self):
        (mod.ROOT, mod.BACKUP, mod.CANDIDATE, mod.TARGET,
         mod.ORIGINAL, mod.CANDIDATE_SHA, mod.REPORT, mod.mutated) = self.old

    def fake_io(self):
        state = {"restarts":0, "install":None, "mv":0}
        def command(*args):
            if args[:2] == ("systemctl", "is-active"):
                return "active"
            if args[:2] == ("stat", "-c"):
                return "root:root:644"
            if args[:2] == ("df", "-Pk"):
                return "Filesystem 1024-blocks Used Available Capacity Mounted on\nX 500000 100 499900 1% /"
            raise AssertionError(args)
        def sudo(*args):
            if args == ("true",):
                return ""
            if args[:1] == ("install",):
                src, dst = Path(args[-2]),Path(args[-1])
                dst.write_bytes(src.read_bytes())
                state["install"] = src.name
                return ""
            if args[:2] == ("mv", "-f"):
                Path(args[2]).replace(Path(args[3]))
                state["mv"] += 1
                return ""
            if args[:2] == ("systemctl", "restart"):
                state["restarts"] += 1
                return ""
            if args[:2] == ("rm", "-f"):
                Path(args[2]).unlink(missing_ok=True)
                return ""
            raise AssertionError(args)
        return state, command, sudo

    def test_import_is_inert(self):
        self.assertTrue(callable(mod.execute))
        self.assertEqual((self.root/"assessment_api.py").read_bytes(),self.raw["assessment_api.py"])

    def test_sha_drift_blocks_before_write(self):
        (self.root/"server.py").write_text("changed")
        state, command, sudo = self.fake_io()
        with patch.object(mod,"run",side_effect=command),patch.object(mod,"sudo",side_effect=sudo),patch.object(mod.os,"geteuid",return_value=1000):
            self.assertEqual(mod.execute(),2)
        self.assertEqual(mod.REPORT["status"],"HOLD_NO_PRODUCTION_WRITE")
        self.assertEqual(state["mv"],0)
        self.assertEqual(state["restarts"],0)

    def test_stale_non_target_backups_are_permitted(self):
        (self.backup/"server.py").write_text("historical backup\n")
        (self.backup/"assessment_state.py").write_text("historical backup\n")
        state, command, sudo = self.fake_io()
        def http(path):
            return 200 if path=="/health" else 403
        with patch.object(mod,"run",side_effect=command),patch.object(mod,"sudo",side_effect=sudo),patch.object(mod,"http_status",side_effect=http),patch.object(mod,"authenticated_echo_check"),patch.object(mod.os,"geteuid",return_value=1000):
            self.assertEqual(mod.execute(),0)
        self.assertEqual((self.root/"server.py").read_bytes(),self.raw["server.py"])
        self.assertEqual((self.root/"assessment_state.py").read_bytes(),self.raw["assessment_state.py"])
        self.assertEqual(state["mv"],1)

    def test_target_backup_drift_holds_before_write(self):
        (self.backup/"assessment_api.py").write_text("stale")
        state, command, sudo = self.fake_io()
        with patch.object(mod,"run",side_effect=command),patch.object(mod,"sudo",side_effect=sudo),patch.object(mod.os,"geteuid",return_value=1000):
            self.assertEqual(mod.execute(),2)
        self.assertEqual(mod.REPORT["status"],"HOLD_NO_PRODUCTION_WRITE")
        self.assertEqual(state["mv"],0)
        self.assertEqual(state["restarts"],0)

    def test_preflight_error_code_is_reported_without_writes(self):
        (self.root/"server.py").write_text("changed")
        state, command, sudo = self.fake_io()
        with patch.object(mod,"run",side_effect=command),patch.object(mod,"sudo",side_effect=sudo),patch.object(mod.os,"geteuid",return_value=1000):
            self.assertEqual(mod.execute(),2)
        self.assertEqual(mod.REPORT["error_code"], "HOLD_SHA_DRIFT_server.py")
        self.assertEqual(mod.REPORT["error_stage"], "PREFLIGHT")
        self.assertEqual(state["mv"],0)

    def test_arbitrary_exception_text_is_not_disclosed(self):
        state, command, sudo = self.fake_io()
        with patch.object(mod.os,"geteuid",return_value=1000),patch.object(mod,"verified",side_effect=RuntimeError("private-token-do-not-log")):
            self.assertEqual(mod.execute(),2)
        self.assertEqual(mod.REPORT["error_type"], "RuntimeError")
        self.assertNotIn("error_code",mod.REPORT)
        self.assertEqual(mod.REPORT["status"],"HOLD_NO_PRODUCTION_WRITE")

    def test_success_replaces_only_server_and_checks_health(self):
        state, command, sudo = self.fake_io()
        def http(path):
            return 200 if path=="/health" else 403
        with patch.object(mod,"run",side_effect=command),patch.object(mod,"sudo",side_effect=sudo),patch.object(mod,"http_status",side_effect=http),patch.object(mod,"authenticated_echo_check"),patch.object(mod.os,"geteuid",return_value=1000):
            self.assertEqual(mod.execute(),0)
        self.assertEqual(mod.REPORT["status"],"DEPLOY_HEALTH_AUTH_AND_5M_ECHO_PASS")
        self.assertEqual((self.root/"assessment_api.py").read_bytes(),self.candidate_raw)
        self.assertEqual((self.root/"server.py").read_bytes(),self.raw["server.py"])
        self.assertEqual(state["restarts"],1)

    def test_failing_postflight_automatically_restores_backup(self):
        state, command, sudo = self.fake_io()
        def http(path):
            if path == "/health" and state["restarts"]==1:
                return 503
            return 200 if path=="/health" else 403
        with patch.object(mod,"run",side_effect=command),patch.object(mod,"sudo",side_effect=sudo),patch.object(mod,"http_status",side_effect=http),patch.object(mod,"authenticated_echo_check"),patch.object(mod.os,"geteuid",return_value=1000),patch.object(mod.time,"sleep",return_value=None):
            self.assertEqual(mod.execute(),2)
        self.assertEqual(mod.REPORT["status"],"ROLLED_BACK_SAFE")
        self.assertEqual(mod.REPORT["rollback"],"PASS")
        self.assertEqual((self.root/"assessment_api.py").read_bytes(),self.raw["assessment_api.py"])
        self.assertEqual(state["restarts"],2)

if __name__=="__main__":
    unittest.main()
