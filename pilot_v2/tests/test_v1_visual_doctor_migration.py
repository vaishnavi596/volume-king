"""V2 local-only V1 visual/Help Doctor migration safety regression."""
import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(ROOT))
import local_help_doctor as doctor
import v1_visual_style as style

class V1VisualDoctorMigration(unittest.TestCase):
    def test_modules_compile_and_no_old_provider_or_server_settings(self):
        for name in ("v1_visual_style.py", "local_help_doctor.py"):
            source = (ROOT / name).read_text(encoding="utf-8")
            ast.parse(source, filename=name)
            tree = ast.parse(source)
            imports = [n.module for n in ast.walk(tree)
                       if isinstance(n, ast.ImportFrom)]
            imports += [a.name for n in ast.walk(tree)
                        if isinstance(n, ast.Import) for a in n.names]
            for prohibited in ("market_feed", "server_feed", "secure_credentials",
                               "requests", "httpx", "urllib", "socket",
                               "paper_engine", "oracle_226_client"):
                self.assertNotIn(prohibited, imports)
            self.assertNotIn("access_token", source)
            self.assertNotIn("api_secret", source)
            self.assertNotIn("Yahoo", source)
            self.assertNotIn("Angel One", source)

    def test_v1_color_tokens_and_readable_size(self):
        self.assertEqual(style.BG, "#080F18")
        self.assertEqual(style.GOLD, "#E9B949")
        self.assertEqual(style.PANEL, "#102735")
        self.assertEqual(style.GREEN, "#16C784")
        self.assertEqual(style.RED, "#FF7890")
        self.assertGreaterEqual(style.BODY_SIZE, 14)

    def test_help_doctor_classifies_without_leaking_input(self):
        message = "HTTP 429 token=PRIVATE-SECRET"
        code, cause, action = doctor.diagnose(message)
        self.assertEqual(code, "BK-DHAN-429")
        self.assertNotIn("PRIVATE-SECRET", cause + action)
        self.assertEqual(doctor.diagnose("HTTP 401")[0], "BK-AUTH-401")
        self.assertEqual(doctor.diagnose("HTTP 422")[0], "BK-MAP-422")
        self.assertEqual(doctor.diagnose("no verified candles")[0], "BK-CANDLES")
        self.assertNotIn("Angel", doctor.help_for("Options"))

    def test_scanner_option_help_and_historical_labels_preserve_source_gate(self):
        source = (ROOT / "main.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn('tooltip="Scanner Help"', source)
        self.assertIn('on_click=lambda e: open_help("Scanner")', source)
        self.assertIn('tooltip="Options Help"', source)
        self.assertIn('on_click=lambda e: open_help("Options")', source)
        self.assertIn('ft.Text("Trusted completed cache only", color=MUTED', source)
        self.assertIn('ft.Text("Completed OHLC candles · historical / unverified",', source)
        self.assertIn('ft.Text("Historical close-price chart · NOT live / not a verified trade signal",', source)
        self.assertEqual(source.count('ft.NavigationDestination('), 3)
        self.assertNotIn('ServerAngelFeed(', source)
        self.assertNotIn('get_yahoo(', source)

    def test_context_help_uses_settings_tab_and_no_network(self):
        source = (ROOT / "main.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        self.assertIn("def open_help(topic):", source)
        self.assertIn('help_topic[0] = topic', source)
        self.assertIn('current[0] = 2', source)
        self.assertIn('page.navigation_bar.selected_index = 2', source)
        self.assertIn('open_help("Dashboard")', source)
        self.assertIn('open_help("Watchlist")', source)
        self.assertEqual(source.count('ft.NavigationDestination('), 3)
        self.assertNotIn('page.run_task(open_help', source)
        self.assertNotIn('from server_feed import', source)

    def test_dashboard_watchlist_reuse_v1_visual_shell_without_provider(self):
        source = (ROOT / "main.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn('ft.Text("System Health", color=GOLD', source)
        self.assertIn('ft.Text(row["symbol"] + "  " + row["price"],', source)
        self.assertIn('ft.Text(row["candle"], size=14, color=WHITE)', source)
        self.assertIn('ft.Text(row["filter_text"], size=14, color=MUTED)', source)
        self.assertIn('ft.Text("Scanner", size=17, color=GOLD', source)
        self.assertIn('ft.Text("Master Device Control", size=16, color=GOLD', source)
        self.assertIn('v1_card(ft, [', source)
        self.assertEqual(source.count('ft.NavigationDestination('), 3)
        self.assertNotIn("ServerAngelFeed(", source)
        self.assertNotIn("get_yahoo(", source)

    def test_local_help_topic_contract_is_non_network_and_non_secret(self):
        source = (ROOT / "main.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        self.assertIn("def choose_help(e):", source)
        self.assertIn('help_topic = ["Dashboard"]', source)
        self.assertIn("on_change=choose_help", source)
        self.assertIn("help_for(help_topic[0])", source)
        self.assertIn("v1_card(ft, [ft.Text(help_topic[0]", source)
        self.assertIn('diagnose(storage_error or smart_error or "unavailable")[2]', source)
        self.assertIn("ft.NavigationDestination", source)
        self.assertNotIn("page.run_task(fetch_help", source)
        for topic in ("Dashboard", "Watchlist", "Scanner", "Super Five",
                      "Options", "Filters", "Settings"):
            self.assertTrue(doctor.help_for(topic))
        self.assertNotIn("token=", doctor.help_for("Settings"))

    def test_flet_main_uses_safe_style_and_doctor_not_old_server(self):
        source = (ROOT / "main.py").read_text(encoding="utf-8")
        ast.parse(source)
        for expected in ("apply_v1_theme(page, ft)", "v1_header(ft, APP_VERSION_NAME, on_notices_click=open_local_notices)",
                         "v1_card(ft,", "diagnose(", "help_for("):
            self.assertIn(expected, source)
        for forbidden in ("from market_feed import", "from server_feed import",
                          "import secure_credentials", "get_yahoo(",
                          "ServerAngelFeed(", "submit_order("):
            self.assertNotIn(forbidden, source)

if __name__ == "__main__":
    unittest.main()
