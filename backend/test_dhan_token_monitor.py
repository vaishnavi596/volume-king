"""Offline regression tests for the read-only Oracle Dhan token monitor.

Run: python3 -m unittest discover -s backend -p 'test_dhan_token_monitor.py'
No network, token file, Oracle deployment or credentials required.
"""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
from datetime import datetime

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

    def test_no_token_file_returns_unknown_without_network(self):
        with patch.object(monitor.TOKEN_PATH.__class__, "read_text", side_effect=FileNotFoundError):
            with patch.object(monitor, "urlopen") as network:
                self.assertEqual(monitor.main(), 3)
                network.assert_not_called()


if __name__ == "__main__":
    unittest.main()
