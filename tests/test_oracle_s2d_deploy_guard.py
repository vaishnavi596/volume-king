"""S2D deployment guard regression: never run on production during CI."""
import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"deploy_oracle_s2d_quote_gate.py"

class S2DDeployGuardTests(unittest.TestCase):
    def test_deployer_has_explicit_apply_and_exact_hash_guards(self):
        source=SCRIPT.read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn('p.add_argument("--apply",action="store_true"',source)
        self.assertIn('if not apply:',source)
        self.assertIn('print("PRODUCTION_CHANGED: NO")',source)
        self.assertIn('if digest(TARGET)!=BEFORE_SHA:',source)
        self.assertIn('if digest(PROPOSED)!=AFTER_SHA:',source)
        self.assertIn('if digest(backup)!=BEFORE_SHA:',source)
        self.assertIn('atomic_copy(backup,TARGET,meta)',source)
        self.assertIn('ROLLBACK_ORIGINAL_SHA_MATCH:',source)
        self.assertIn('LIVE_DHAN_AUTH_AND_QUOTES: NOT_CHECKED',source)
        self.assertNotIn('place_order(',source)

    def test_atomic_install_and_safe_backups_defined(self):
        source=SCRIPT.read_text(encoding="utf-8")
        self.assertIn('os.replace(tmp,dst)',source)
        self.assertIn('os.fsync(stream.fileno())',source)
        self.assertIn('os.chown(tmp, metadata.st_uid,metadata.st_gid)',source)
        self.assertIn('os.chmod(backup,0o600)',source)
        self.assertIn('systemctl","restart","bot-king.service"',source)
