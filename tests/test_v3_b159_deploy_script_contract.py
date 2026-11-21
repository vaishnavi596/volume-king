"""B159 operator deployment: syntax and strict Clone/V1 isolation, no live server calls."""
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"ops"/"deploy_v3_b159_clone_upstream_diagnostics_guarded.sh"
AUDIT=ROOT/"ops"/"audit_v3_sensex_v1_route_isolation_readonly.sh"

class B159DeployScriptContractTests(unittest.TestCase):
    def test_shell_syntax_only(self):
        for file in (SCRIPT,AUDIT):
            with self.subTest(file=file.name):
                result=subprocess.run(["bash","-n",str(file)],capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)
    def test_two_reviewed_files_and_fail_closed_blobs(self):
        src=SCRIPT.read_text(encoding="utf-8")
        for required in ("OLD_FEED_BLOB=","OLD_GATEWAY_BLOB=","NEW_FEED_BLOB=",
                         "NEW_GATEWAY_BLOB=","BLOCKED_DEPLOYED_BLOB_DIFFERS",
                         "ROLLBACK_FILES_VERIFIED=YES","DEPLOY_FAILED_ROLLBACK_BEGIN",
                         "NO_V1_CONFIG_EDIT=YES","NO_MARKET_PROVIDER_REQUESTS_SENT=YES"):
            self.assertIn(required,src)
        self.assertNotIn("systemctl restart \"$V1\"",src)
        self.assertNotIn("systemctl stop \"$V1\"",src)
        self.assertIn('sudo -n systemctl restart "$SERVICE"',src)
    def test_oracle_readonly_script_has_new_safe_categories(self):
        src=AUDIT.read_text(encoding="utf-8")
        for category in ("upstream_http_4xx","upstream_http_5xx","upstream_transport",
                         "upstream_payload","upstream_rejection","missing_segment"):
            self.assertIn(category,src)

if __name__=="__main__":unittest.main()
