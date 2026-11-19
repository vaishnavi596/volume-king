"""No credentials, guessed master role, or fake LIVE claims in Settings."""
import ast
import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from secure_https_reader import V2ReadonlyHTTPSReader
from app_connection_status import local_connection_state


class LocalConnectionStatusTests(unittest.TestCase):
    def test_no_login_defaults_to_unconfigured_without_live_claim(self):
        info = local_connection_state()
        self.assertEqual(info["code"], "NOT_CONFIGURED")
        self.assertFalse(info["live"])
        self.assertIn("WAIT", info["label"])

    def test_local_bearer_is_never_claimed_authenticated_or_exposed(self):
        secret = "s" * 48
        class NoNetwork:
            def open(self, *args, **kwargs):
                raise AssertionError("Status must not perform any network request")
        reader = V2ReadonlyHTTPSReader(
            "https://example.test", secret, opener=NoNetwork())
        info = local_connection_state(reader)
        self.assertEqual(info["code"], "LOCAL_BEARER_UNVERIFIED")
        self.assertFalse(info["live"])
        self.assertNotIn(secret, repr(info))
        reader.invalidate()
        revoked = local_connection_state(reader)
        self.assertEqual(revoked["code"], "SIGN_IN_REQUIRED")
        self.assertIn("cached HIST", revoked["label"])
        self.assertNotIn(secret, repr(revoked))

    def test_app_settings_only_renders_offline_status_without_reader_constructor(self):
        main = (SRC / "main.py").read_text(encoding="utf-8")
        ast.parse(main)
        self.assertIn("from app_connection_status import local_connection_state", main)
        self.assertIn("local_connection_state(device_session_reader[0])", main)
        self.assertIn("device_session_reader = [None]", main)
        self.assertNotIn("V2ReadonlyHTTPSReader(", main)
        self.assertNotIn("session_active = True", main)
        self.assertIn("Enable / Disable / Revoke require verified device login", main)

    def test_unknown_connection_handle_is_rejected(self):
        for value in ("token", {}, object(), True):
            with self.subTest(value=type(value).__name__), self.assertRaises(ValueError):
                local_connection_state(value)


if __name__ == "__main__":
    unittest.main()
