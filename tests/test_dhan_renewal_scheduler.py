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

    def test_due_metadata_dry_run_never_rotates(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "expiry.json"
            expiry = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
            save_expiry_metadata(target, expiry)
            with patch("backend.dhan_renewal_scheduler.renew_web_token") as renew:
                self.assertEqual(main(["--expiry-file", str(target)]), 0)
                renew.assert_not_called()

    def test_due_metadata_execute_calls_guarded_renewal(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "expiry.json"
            token = Path(directory) / "token"
            expiry = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
            save_expiry_metadata(target, expiry)
            with patch.dict("os.environ", {"DHAN_CLIENT_ID": "offline-test-id"}), \
                 patch("backend.dhan_renewal_scheduler.renew_web_token",
                       return_value={"profile_verified": True}) as renew:
                self.assertEqual(main(["--expiry-file", str(target),
                                       "--token-file", str(token), "--execute"]), 0)
                renew.assert_called_once_with("offline-test-id", token, expiry_path=target)

    def test_due_metadata_execute_failure_returns_nonzero(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "expiry.json"
            expiry = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
            save_expiry_metadata(target, expiry)
            with patch.dict("os.environ", {"DHAN_CLIENT_ID": "offline-test-id"}), \
                 patch("backend.dhan_renewal_scheduler.renew_web_token",
                       side_effect=ValueError("simulated failure")):
                self.assertEqual(main(["--expiry-file", str(target), "--execute"]), 1)

    def test_execute_unverified_profile_returns_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "expiry.json"
            expiry = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
            save_expiry_metadata(target, expiry)
            with patch.dict("os.environ", {"DHAN_CLIENT_ID": "offline-test-id"}), \
                 patch("backend.dhan_renewal_scheduler.renew_web_token",
                       return_value={"profile_verified": False}) as renew:
                self.assertEqual(main(["--expiry-file", str(target), "--execute"]), 1)
                renew.assert_called_once()

    def test_execute_malformed_result_returns_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "expiry.json"
            expiry = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
            save_expiry_metadata(target, expiry)
            with patch.dict("os.environ", {"DHAN_CLIENT_ID": "offline-test-id"}), \
                 patch("backend.dhan_renewal_scheduler.renew_web_token",
                       return_value=None):
                self.assertEqual(main(["--expiry-file", str(target), "--execute"]), 1)

    def test_bad_expiry_fails_closed(self):
        with self.assertRaises(ValueError):
            scheduled_decision("dhan_web", "not-a-date", now=self.now)


if __name__ == "__main__":
    unittest.main()
