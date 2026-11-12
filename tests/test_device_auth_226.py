"""Offline PIN/session primitive tests; production auth routes are not enabled."""
import importlib.util
import unittest
from pathlib import Path
_module_path = Path(__file__).resolve().parents[1] / "backend" / "device_auth_226.py"
_spec = importlib.util.spec_from_file_location("botking_226_device_auth", _module_path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
DeviceAuthError = _module.DeviceAuthError
hash_pin = _module.hash_pin
verify_pin = _module.verify_pin
new_session_token = _module.new_session_token
session_token_digest = _module.session_token_digest


class DeviceAuth226Tests(unittest.TestCase):
    def test_pin_verifier(self):
        record = hash_pin("123456")
        self.assertTrue(verify_pin("123456", record))
        self.assertFalse(verify_pin("123457", record))
        self.assertNotIn("123456", repr(record))

    def test_pin_rejects_unicode_digits(self):
        with self.assertRaises(DeviceAuthError):
            hash_pin("１２３４５６")

    def test_pin_rejects_non_six_digit_input(self):
        for value in ("12345", "1234567", "abc123", None):
            with self.subTest(value=value), self.assertRaises(DeviceAuthError):
                hash_pin(value)

    def test_unique_salts(self):
        self.assertNotEqual(hash_pin("123456")["salt"], hash_pin("123456")["salt"])

    def test_corrupt_record_fails_closed(self):
        self.assertFalse(verify_pin("123456", {"algorithm": "pbkdf2-sha256"}))

    def test_random_session_digest(self):
        a, b = new_session_token(), new_session_token()
        self.assertNotEqual(a, b)
        self.assertNotEqual(session_token_digest(a), a)
        self.assertEqual(len(session_token_digest(a)), 64)


if __name__ == "__main__":
    unittest.main()
