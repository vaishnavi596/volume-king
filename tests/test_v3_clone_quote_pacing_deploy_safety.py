"""Offline safety gate for audit-first V3 Clone-only source deployment."""
from pathlib import Path
import re
import unittest
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=(ROOT/"ops/v3_clone_quote_pacing_guarded_20261122.sh").read_text()
GATEWAY=(ROOT/"backend/clone_v2_gateway.py").read_bytes()

class V3CloneQuoteDeploymentSafety(unittest.TestCase):
    def test_pinned_git_blob_is_exact_candidate(self):
        import hashlib
        digest=hashlib.sha1(b"blob "+str(len(GATEWAY)).encode()+b"\0"+GATEWAY).hexdigest()
        self.assertIn("EXPECTED_NEW="+digest,SCRIPT)
        self.assertIn('[[ "$(blob "$WORK/$TARGET")" == "$EXPECTED_NEW" ]]',SCRIPT)
    def test_audit_only_default_and_explicit_baseline(self):
        self.assertIn('MODE=${1:---audit}'.replace("\\",""),SCRIPT)
        self.assertIn('[[ "$MODE" == --audit || "$MODE" == --apply ]]',SCRIPT)
        self.assertIn('[[ "$EXPECTED_OLD" =~ ^[a-f0-9]{40}$ && "$EXPECTED_OLD" == "$LIVE_BLOB" ]]',SCRIPT)
        self.assertIn('if [[ "$MODE" == --audit ]]; then',SCRIPT)
        self.assertIn('V3_CLONE_GATEWAY_SOURCE=DIFFERENT_NO_WRITE',SCRIPT)
    def test_clone_only_reversible_health_and_no_provider_poll(self):
        for text in ('ROOT=/home/opc/botking-clone-v2-runtime',
                     'SERVICE=botking-clone-v2.service',
                     'V1=bot-king.service',
                     'cp -p "$ROOT/$TARGET" "$WORK/$TARGET.rollback"',
                     'trap rollback ERR', 'V3_CLONE_ROLLBACK_ATTEMPTED=YES',
                     'V3_V1_UNCHANGED_AND_HEALTHY=YES',
                     'V3_NO_DHAN_API_OR_TRADE_REQUEST=YES',
                     'http://127.0.0.1:8002/clone-v2/health',
                     'http://127.0.0.1:8000/health'):
            self.assertIn(text,SCRIPT)
        self.assertNotIn('sudo -n systemctl restart "$V1"',SCRIPT)
        self.assertNotIn('market/quotes',SCRIPT)
        self.assertNotIn('market/candles',SCRIPT)

if __name__=="__main__":
    unittest.main()
