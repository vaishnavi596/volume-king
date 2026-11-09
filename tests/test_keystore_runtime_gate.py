"""Prevent shipping a Python-only Keystore control without native registration."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RuntimeIntegrationGate(unittest.TestCase):
    def test_flutter_control_factory_matches_python_control_name(self):
        dart = (ROOT / "prototype/flet_keystore/lib/src/create_control.dart").read_text()
        python = (ROOT / "src/keystore_control.py").read_text()
        self.assertIn('args.control.type != \'botkingkeystore\'', dart)
        self.assertIn('return "botkingkeystore"', python)

    def test_native_storage_uses_encrypted_preferences(self):
        dart = (ROOT / "prototype/flet_keystore/lib/src/keystore_control.dart").read_text()
        self.assertIn("FlutterSecureStorage", dart)
        self.assertIn("encryptedSharedPreferences: true", dart)
        self.assertIn("botking.dhan.server_access.v1", dart)

    def test_main_app_does_not_claim_native_storage_is_registered(self):
        # Explicit release gate: this experiment cannot be merged as a secure
        # auto-login feature until the real Flet build registers the factory.
        main = (ROOT / "src/main.py").read_text()
        self.assertNotIn("VerifiedNativeCredentialStore(", main)


if __name__ == "__main__":
    unittest.main()
