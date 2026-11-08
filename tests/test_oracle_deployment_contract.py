"""Guard Oracle installer parity with the read-only Dhan gateway.

Static regression checks only: no Oracle connection, credentials, or APK build.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OracleDhanDeploymentContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.installer = (ROOT / "backend" / "install-oracle.sh").read_text(encoding="utf-8")
        cls.server = (ROOT / "backend" / "server.py").read_text(encoding="utf-8")

    def test_readonly_audit_never_outputs_credentials(self):
        audit = (ROOT / "backend" / "audit-oracle-dhan-readonly.sh").read_text(encoding="utf-8")
        self.assertIn('runuser -u "$user" -- test -r "$token"', audit)
        self.assertIn('local gateway health:', audit)
        self.assertNotIn('cat "$token"', audit)
        self.assertNotIn('echo "$token"', audit)
        self.assertNotIn('chmod ', audit)
        self.assertNotIn('chown ', audit)

    def test_required_dhan_adapter_is_staged_and_installed(self):
        self.assertIn('"$base/backend/dhan_feed.py" -o "$stage/dhan_feed.py"', self.installer)
        self.assertIn('"$stage/dhan_feed.py" "$appdir/dhan_feed.py"', self.installer)
        self.assertIn('"$stage/dhan_feed.py"', self.installer)

    def test_dhan_adapter_is_in_backup_and_rollback(self):
        self.assertIn('for entry in market_feed.py dhan_feed.py; do', self.installer)
        self.assertIn('"$backup/$entry" "$appdir/$entry"', self.installer)

    def test_failed_dhan_proxy_check_restores_previous_gateway(self):
        self.assertIn('if test "$dhan_code" != 403; then', self.installer)
        self.assertIn('        rollback\n        exit 1', self.installer)
        self.assertIn('rollback() {\n    trap - ERR', self.installer)

    def test_dhan_api_is_proxied_and_callback_preserved(self):
        for endpoint in ("/dhan/status", "/dhan/ltp", "/dhan/ltp-batch", "/dhan/intraday"):
            self.assertIn(endpoint, self.server)
        self.assertIn("location /dhan/ {", self.installer)
        self.assertIn("location = /dhan/callback {", self.installer)
        self.assertIn("proxy_pass http://127.0.0.1:8000;", self.installer)
        self.assertIn("nginx -t", self.installer)


if __name__ == "__main__":
    unittest.main()
