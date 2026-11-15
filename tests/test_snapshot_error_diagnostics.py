"""Safe and actionable Dhan snapshot diagnostics: no credential disclosure."""
import unittest
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from market_feed import FeedError
from feed_health import safe_error


class SnapshotErrorDiagnosisTests(unittest.TestCase):
    def test_stale_or_missing_snapshot_has_actionable_message(self):
        msg=safe_error(FeedError("Oracle Dhan snapshot missing, stale or invalid"))
        self.assertIn("Oracle snapshot",msg)
        self.assertIn("server collection",msg)
        self.assertNotIn("Data request failed",msg)

    def test_no_quotes_and_invalid_price_are_separate_causes(self):
        self.assertIn("no equity quotes",safe_error(FeedError("Oracle Dhan snapshot contains no quotes")))
        self.assertIn("invalid equity price",safe_error(FeedError("Invalid Oracle Dhan snapshot quote")))

    def test_unrecognized_error_does_not_disclose_untrusted_text(self):
        err=FeedError("unknown gateway response SECRET_TOKEN_123")
        self.assertNotIn("SECRET_TOKEN_123",safe_error(err))

if __name__=="__main__":
    unittest.main()
