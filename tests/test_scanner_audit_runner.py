"""Exercise the read-only handoff wrapper with local fixture downloads only."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT/"backend"/"run-scanner-audit.sh"


class ScannerAuditRunnerTests(unittest.TestCase):
    def test_invalid_revision_stops_before_any_download(self):
        result = subprocess.run(["bash", str(RUNNER), "not-a-commit"],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("no requests made", result.stdout)

    def test_help_downloads_only_four_pinned_sources_and_never_calls_provider(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            curl = folder/"curl"
            curl.write_text('''#!/usr/bin/env python3
import os, pathlib, sys
from urllib.parse import urlsplit
args=sys.argv[1:]
url=next(x for x in args if x.startswith("https://"))
parsed=urlsplit(url)
assert parsed.hostname=="raw.githubusercontent.com"
parts=parsed.path.strip("/").split("/")
assert parts[:3]==["vaishnavi596","volume-king","a"*40]
relative="/".join(parts[3:])
assert relative in {"backend/audit-dhan-51-candles.py","backend/check-dhan-live.py",
                    "src/server_feed.py","src/scanner_engine.py"}
destination=pathlib.Path(args[args.index("-o")+1])
destination.write_bytes((pathlib.Path(os.environ["AUDIT_FIXTURE_ROOT"])/relative).read_bytes())
with open(os.environ["AUDIT_DOWNLOAD_LOG"],"a") as log:log.write(relative+"\\n")
''')
            curl.chmod(0o700)
            log = folder/"downloads.txt"
            env = dict(os.environ, PATH=str(folder)+os.pathsep+os.environ["PATH"],
                       AUDIT_FIXTURE_ROOT=str(ROOT), AUDIT_DOWNLOAD_LOG=str(log))
            result = subprocess.run(["bash", str(RUNNER), "a"*40, "--help"],
                                    env=env, text=True, capture_output=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("--all-symbols", result.stdout)
            self.assertNotIn("Pairing key unavailable", result.stdout)
            self.assertEqual(len(log.read_text().splitlines()), 4)
