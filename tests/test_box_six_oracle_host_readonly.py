"""Check that Box Six Oracle inspection script has no mutation operations."""
import pathlib
import subprocess
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"ops"/"audit_box_six_oracle_readonly.sh"

class BoxSixHostReadOnlyContracts(unittest.TestCase):
    def test_shell_syntax(self):
        run=subprocess.run(["bash","-n",str(SCRIPT)],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)

    def test_no_operations_or_secret_dumps(self):
        text=SCRIPT.read_text()
        self.assertIn("BOX_SIX_STAGING_HOST_GATE=",text)
        self.assertIn("PORT_8766=FREE_FOR_SEPARATE_STAGING",text)
        self.assertIn("FILES_WRITTEN=0",text)
        self.assertIn("SERVICES_CHANGED=0",text)
        self.assertIn("127.0.0.1:",text)
        for forbidden in ("systemctl restart ", "systemctl start ", "systemctl stop ",
                          "systemctl reload ", "systemctl enable ", "nginx -s reload",
                          "curl ", "cat /etc/bot-king", "printenv", "env |", "set -x",
                          "sudo ", "scp ", "rm -rf", "chmod ", "chown ",
                          "tee ", "touch ", "mkdir ", "sed -i", "pip install"):
            self.assertNotIn(forbidden,text,forbidden)

if __name__=="__main__":
    unittest.main()
