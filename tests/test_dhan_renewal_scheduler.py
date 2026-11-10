"""Offline tests for expiry-gated Dhan renewal scheduling."""
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from datetime import timedelta
from backend.dhan_expiry_store import save_expiry_metadata
from backend.dhan_renewal_scheduler import main
from datetime import datetime, timezone
from backend.dhan_renewal_scheduler import scheduled_decision


class RenewalSchedulerTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 10, 8, 0, tzinfo=timezone.utc)

    def test_early_renewal_waits(self):
        result = scheduled_decision("dhan_web", "2026-11-11T12:01:00+05:30", now=self.now)
        self.assertEqual(result["state"], "valid")

    def test_due_web_token(self):
        result = scheduled_decision("dhan_web", "2026-11-10T15:00:00+05:30", now=self.now)
        self.assertEqual(result["state"], "renewal_due")

    def test_unknown_provenance_blocks(self):
        result = scheduled_decision("unknown", "2026-11-10T15:00:00+05:30", now=self.now)
        self.assertFalse(result["renew_token_allowed"])

    def test_expired_token_blocks(self):
        result = scheduled_decision("dhan_web", "2026-11-10T12:00:00+05:30", now=self.now)
        self.assertEqual(result["state"], "expired")

    def test_metadata_file_mode_waits_when_not_due(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "expiry.json"
            expiry = (datetime.now(timezone.utc) + timedelta(hours=10)).isoformat()
            save_expiry_metadata(target, expiry)
            self.assertEqual(main(["--expiry-file", str(target)]), 0)

    def test_metadata_file_conflicts_with_manual_expiry(self):
        self.assertEqual(main(["--expiry-file", "/tmp/missing-expiry",
                               "--source", "dhan_web", "--expires-at",
                               "2026-11-11T12:01:00+05:30"]), 1)

    def test_missing_metadata_blocks(self):
        self.assertEqual(main(["--expiry-file", "/tmp/nonexistent-botking-expiry"]), 1)

    def test_bad_expiry_fails_closed(self):
        with self.assertRaises(ValueError):
            scheduled_decision("dhan_web", "not-a-date", now=self.now)


if __name__ == "__main__":
    unittest.main()
