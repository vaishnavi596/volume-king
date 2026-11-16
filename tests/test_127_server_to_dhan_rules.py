"""127 server-to-Dhan ports, credentials and read-only contract guard."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
BACKEND=ROOT/"backend"


class ServerToDhanRulesTests(unittest.TestCase):
    def test_operator_audit_syntax_and_both_token_sources(self):
        shell=BACKEND/"audit-oracle-dhan-readonly.sh"
        source=shell.read_text(encoding="utf-8")
        if shutil.which("bash"):
            result=subprocess.run(["bash","-n",str(shell)],capture_output=True,
                                  text=True,timeout=10,check=False)
            self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn("DHAN_SESSION_FILE=",source)
        self.assertIn('has_oauth=1',source)
        self.assertIn('has_token=1',source)
        self.assertIn('(( ! has_token && ! has_oauth ))',source)
        self.assertIn('runuser -u "$user" -- test -r "$session_file"',source)
        self.assertIn('runuser -u "$user" -- test -r "$token"',source)
        self.assertNotIn('cat "$token"',source)
        self.assertNotIn('source "$envfile"',source)
        self.assertIn("ss -H -ltn '( sport = :8000 )'",source)
        self.assertIn("127[.]0[.]0[.]1:8000",source)
        self.assertIn("'https://api.dhan.co/v2/profile'",source)
        self.assertIn("--noproxy '*'",source)
        self.assertNotIn("access-token:",source)


    def test_gateway_ports_and_pairing_header_separated_from_dhan_token(self):
        installer=(BACKEND/"install-oracle.sh").read_text(encoding="utf-8")
        server=(BACKEND/"server.py").read_text(encoding="utf-8")
        adapter=(BACKEND/"dhan_feed.py").read_text(encoding="utf-8")
        self.assertIn("--host 127.0.0.1 --port 8000",installer)
        # Per-process quote gate requires the service's documented single worker.
        self.assertIn("--workers 1",installer)
        self.assertIn("listen 443 ssl",installer)
        self.assertIn("location /dhan/ {",installer)
        self.assertIn("location /v2/ {",installer)
        self.assertIn('x_botking_key: Optional[str] = Header(default=None)',server)
        self.assertIn('hmac.compare_digest',server)
        self.assertIn('"access-token": self._token',adapter)
        self.assertIn('"client-id": self.client_id',adapter)
        self.assertIn('QUOTE_MIN_INTERVAL_SECONDS = 1.05',adapter)
        self.assertIn('allow_redirects=False',server)
        self.assertNotIn("place_order(",adapter)


if __name__=="__main__":
    unittest.main()
