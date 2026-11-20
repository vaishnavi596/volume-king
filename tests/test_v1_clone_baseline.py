"""Clone-baseline contract: V1 visual features intact, only server SETTINGS hidden.

This deliberately does not remove Yahoo, Angel One or V1's original UI.
The separate APK is for physical UI acceptance, not authenticated trading.
"""
import ast
import pathlib
import tomllib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class ExactV1CloneBaseline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "src/main.py").read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)
        cls.config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    def test_all_original_providers_remain_in_source(self):
        for token in ("ServerAngelFeed", "get_yahoo(", "Yahoo Finance", "Angel One"):
            self.assertIn(token, self.source)

    def test_old_server_configuration_not_rendered_or_saved(self):
        self.assertNotIn('label="My BOT KING server HTTPS address (optional)"', self.source)
        self.assertNotIn('label="Server access key (not saved)"', self.source)
        self.assertNotIn('credential_column, api_url, server_access, server_trust,', self.source)
        self.assertNotIn('(api_url,"api_url")', self.source)
        self.assertIn('prefs.pop("api_url", None)', self.source)
        self.assertIn('"server_access","api_url"', self.source)

    def test_full_v1_sections_and_navigation_preserved(self):
        for text in ('heading("Settings")', 'def settings():', 'def main(', 'option_chart_panel()', "heading(\"Settings\")", 'def get_yahoo('):
            self.assertIn(text, self.source)
        self.assertIn("def get_yahoo(", self.source)

    def test_clone_package_is_distinct(self):
        self.assertEqual(self.config["project"]["name"], "bot-king-v1-clone")
        self.assertEqual(self.config["tool"]["flet"]["org"], "com.botking.clone")
        self.assertEqual(self.config["tool"]["flet"]["product"], "BOT KING V2 CLONE")


if __name__ == "__main__":
    unittest.main()
