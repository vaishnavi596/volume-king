"""Offline release gates for BOT KING 2.3.67 three-provider recovery."""
from pathlib import Path
import re
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ThreeProviderReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "src/main.py").read_text(encoding="utf-8")
        cls.project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    def test_version_synchronized(self):
        self.assertEqual(self.project["project"]["version"], "2.3.67")
        self.assertRegex(self.app, r'APP_VERSION = "2\\.3\\.67"\\s*# Release fallback;')

    def test_all_three_sources_selectable(self):
        for provider in ("Yahoo Finance", "Broker API", "Dhan"):
            self.assertIn('ft.dropdown.Option("'+provider+'")', self.app)
        self.assertIn('from server_feed import ServerAngelFeed, ServerDhanReadOnly', self.app)

    def test_source_isolation_and_dhan_login(self):
        self.assertIn('prefs.get("source")', self.app)
        self.assertIn('Dhan Login (only if server token missing)', self.app)
        self.assertIn('open_dhan_authorization', self.app)
        self.assertIn('quote_timestamp":None', self.app)

    def test_no_live_orders_misrepresented(self):
        self.assertIn("Live order submission is DISABLED", self.app)
        self.assertIn("historical candidates; not verified live", self.app)

if __name__ == "__main__":
    unittest.main()
