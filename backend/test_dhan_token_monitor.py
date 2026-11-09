"""Offline regression tests for the read-only Oracle Dhan token monitor.

Run: python3 -m unittest discover -s backend -p 'test_dhan_token_monitor.py'
No network, token file, Oracle deployment or credentials required.
"""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta, timezone, timedelta

MODULE = Path(__file__).with_name("check-dhan-token-expiry.py")
spec = importlib.util.spec_from_file_location("dhan_token_monitor", MODULE)
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)


class TokenExpiryParsingTests(unittest.TestCase):
    def test_valid_day_first_expiry(self):
        self.assertEqual(monitor.parse_expiry("10/11/2026 09:43"), datetime(2026, 11, 10, 9, 43))

    def test_valid_expiry_with_seconds(self):
        self.assertEqual(monitor.parse_expiry("10/11/2026 09:43:01"), datetime(2026, 11, 10, 9, 43, 1))

    def test_missing_or_invalid_expiry(self):
        for value in (None, "", "2026-11-10", "32/11/2026 09:43", 123):
            with self.subTest(value=value):
                self.assertIsNone(monitor.parse_expiry(value))

    def test_six_hour_warning_boundary(self):
        now = datetime(2026, 11, 9, 0, 0, tzinfo=timezone.utc)
        # 06:00 UTC is 11:30 in Asia/Kolkata.
        expiry = datetime(2026, 11, 9, 11, 30)
        self.assertEqual(monitor.expiry_alert(expiry, now, "Asia/Kolkata"), (6, True))
        self.assertEqual(monitor.expiry_alert(expiry + timedelta(minutes=1), now, "Asia/Kolkata"), (6, False))

    def test_expired_token_warns(self):
        now = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)
        expiry = datetime(2026, 11, 9, 10, 0)
        self.assertEqual(monitor.expiry_alert(expiry, now, "Asia/Kolkata"), (0, True))

    def test_invalid_timezone_rejected(self):
        with self.assertRaises((KeyError, ValueError)):
            monitor.expiry_alert(datetime(2026, 11, 9), datetime.now(timezone.utc), "Invalid/Zone")

    def test_expiry_state_boundaries(self):
        now = datetime(2026, 11, 10, 0, 0, tzinfo=timezone.utc)
        cases = [
            (timedelta(hours=-1), "expired"),
            (timedelta(seconds=0), "expired"),
            (timedelta(hours=1), "warning"),
            (timedelta(hours=6), "warning"),
            (timedelta(hours=7), "healthy"),
        ]
        for offset, expected in cases:
            with self.subTest(offset=offset):
                expiry = (now + offset).replace(tzinfo=None)
                status, hours = monitor.expiry_assessment(expiry, "UTC", now=now)
                self.assertEqual(status, expected)
                self.assertGreaterEqual(hours, 0)

    def test_timezone_offset_is_not_assumed_utc(self):
        now = datetime(2026, 11, 10, 0, 0, tzinfo=timezone.utc)
        local_expiry = datetime(2026, 11, 10, 9, 0)
        utc_state, _ = monitor.expiry_assessment(local_expiry, "UTC", now=now)
        ist_state, _ = monitor.expiry_assessment(local_expiry, "Asia/Kolkata", now=now)
        self.assertEqual(utc_state, "healthy")
        self.assertEqual(ist_state, "warning")

    def test_invalid_timezone_fails_closed(self):
        with self.assertRaises(KeyError):
            monitor.expiry_assessment(datetime(2026, 11, 10), "Invalid/Timezone")

    def test_no_token_file_returns_unknown_without_network(self):
        with patch.object(monitor.TOKEN_PATH.__class__, "read_text", side_effect=FileNotFoundError):
            with patch.object(monitor, "urlopen") as network:
                self.assertEqual(monitor.main(), 3)
                network.assert_not_called()


if __name__ == "__main__":
    unittest.main()
