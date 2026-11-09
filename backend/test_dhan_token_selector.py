"""No-network Dhan token selector regression tests."""
import unittest
from dhan_token_selector import select_persisted_token


class TokenSelectorTests(unittest.TestCase):
    def test_default_uses_legacy_file_reader_without_verification(self):
        def forbidden(*args, **kwargs):
            self.fail("Verifier called while disabled")
        self.assertEqual(select_persisted_token(
            "/fake", "CLIENT", legacy_reader=lambda p: "FAKE_TOKEN",
            verifier=forbidden), "FAKE_TOKEN")

    def test_strict_mode_requires_matching_verified_token(self):
        calls = []
        def verifier(path, client, provider_timezone=None):
            calls.append((path, client, provider_timezone))
            return "FAKE_TOKEN", object()
        self.assertEqual(select_persisted_token(
            "/fake", "CLIENT", strict=True, provider_timezone="Asia/Kolkata",
            legacy_reader=lambda p: self.fail("Unsafe fallback"), verifier=verifier), "FAKE_TOKEN")
        self.assertEqual(calls, [("/fake", "CLIENT", "Asia/Kolkata")])

    def test_strict_mode_rejects_missing_client(self):
        self.assertEqual(select_persisted_token(
            "/fake", "", strict=True, verifier=lambda *a, **k: self.fail("Unexpected call")), "")

    def test_strict_mode_rejects_network_timeout_no_fallback(self):
        def timeout(*args, **kwargs):
            raise TimeoutError("FAKE_SECRET_TOKEN")
        self.assertEqual(select_persisted_token(
            "/fake", "CLIENT", strict=True, verifier=timeout,
            legacy_reader=lambda p: self.fail("Unsafe fallback")), "")

    def test_strict_mode_rejects_wrong_account(self):
        def wrong_account(*args, **kwargs):
            raise ValueError("Account mismatch")
        self.assertEqual(select_persisted_token(
            "/fake", "CLIENT", strict=True, verifier=wrong_account), "")

    def test_default_missing_file_returns_empty(self):
        def missing(path):
            raise FileNotFoundError(path)
        self.assertEqual(select_persisted_token(
            "/fake", "CLIENT", legacy_reader=missing), "")


if __name__ == "__main__":
    unittest.main()
