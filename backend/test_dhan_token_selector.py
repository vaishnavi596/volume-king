"""No-network Dhan token selector regression tests."""
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
from dhan_token_storage import atomic_store_token
from dhan_token_selector import select_persisted_token, VerifiedTokenCache


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
            return "FAKE_TOKEN", datetime.now(timezone.utc) + timedelta(hours=1)
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

    def test_cache_reuses_verified_token_then_invalidates_on_rotation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "token"
            atomic_store_token(path, "FAKE_TOKEN_ONE")
            calls = []
            clock = [0]
            cache = VerifiedTokenCache(ttl_seconds=30, monotonic=lambda: clock[0])
            def verifier(path, client, provider_timezone=None):
                calls.append(1)
                return Path(path).read_text().strip(), datetime.now(timezone.utc) + timedelta(hours=1)
            def choose():
                return select_persisted_token(path, "CLIENT", strict=True, verifier=verifier, cache=cache)
            self.assertEqual(choose(), "FAKE_TOKEN_ONE")
            self.assertEqual(choose(), "FAKE_TOKEN_ONE")
            self.assertEqual(len(calls), 1)
            atomic_store_token(path, "FAKE_TOKEN_TWO")
            self.assertEqual(choose(), "FAKE_TOKEN_TWO")
            self.assertEqual(len(calls), 2)
            clock[0] = 31
            self.assertEqual(choose(), "FAKE_TOKEN_TWO")
            self.assertEqual(len(calls), 3)

    def test_cache_network_error_never_reuses_expired_entry(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "token"
            atomic_store_token(path, "FAKE_TOKEN")
            clock = [0]
            cache = VerifiedTokenCache(ttl_seconds=10, monotonic=lambda: clock[0])
            calls = [0]
            def verifier(*args, **kwargs):
                calls[0] += 1
                if calls[0] > 1:
                    raise TimeoutError("simulated")
                return "FAKE_TOKEN", datetime.now(timezone.utc) + timedelta(hours=1)
            choose = lambda: select_persisted_token(path, "CLIENT", strict=True, verifier=verifier, cache=cache)
            self.assertEqual(choose(), "FAKE_TOKEN")
            clock[0] = 11
            self.assertEqual(choose(), "")
            self.assertEqual(choose(), "")

    def test_cache_rejects_already_expired_verification(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "token"
            atomic_store_token(path, "FAKE_TOKEN")
            cache = VerifiedTokenCache()
            self.assertEqual(select_persisted_token(path, "CLIENT", strict=True, cache=cache,
                verifier=lambda *a, **k: ("FAKE_TOKEN", datetime.now(timezone.utc) - timedelta(seconds=1))), "")

    def test_default_missing_file_returns_empty(self):
        def missing(path):
            raise FileNotFoundError(path)
        self.assertEqual(select_persisted_token(
            "/fake", "CLIENT", legacy_reader=missing), "")


if __name__ == "__main__":
    unittest.main()
