"""Offline Dhan gateway status verification tests, no credentials or network."""
import unittest
from dhan_status_policy import persisted_session_status


class DhanStatusPolicyTests(unittest.TestCase):
    def test_disabled_never_calls_verifier(self):
        def forbidden(*args, **kwargs):
            self.fail("Verification should be disabled")
        self.assertEqual(persisted_session_status(False, "/unused", "CLIENT", verifier=forbidden), "not_checked")

    def test_missing_client_fails_closed_without_network(self):
        def forbidden(*args, **kwargs):
            self.fail("Missing client must not call verifier")
        self.assertEqual(persisted_session_status(True, "/unused", "", verifier=forbidden), "unverified")

    def test_verified_profile_returns_verified(self):
        calls = []
        def valid(path, client, provider_timezone=None):
            calls.append((path, client, provider_timezone))
            return "FAKE_TOKEN", object()
        self.assertEqual(persisted_session_status(True, "/fake/token", "CLIENT", "Asia/Kolkata", valid), "verified")
        self.assertEqual(calls, [("/fake/token", "CLIENT", "Asia/Kolkata")])

    def test_network_timeout_fails_closed_without_leaking_error(self):
        def timeout(*args, **kwargs):
            raise TimeoutError("SECRET_FAKE_TOKEN")
        result = persisted_session_status(True, "/fake/token", "CLIENT", verifier=timeout)
        self.assertEqual(result, "unverified")
        self.assertNotIn("SECRET", result)

    def test_invalid_profile_fails_closed(self):
        def invalid(*args, **kwargs):
            raise ValueError("FAKE_PROFILE_BODY")
        self.assertEqual(persisted_session_status(True, "/fake/token", "CLIENT", verifier=invalid), "unverified")


if __name__ == "__main__":
    unittest.main()
