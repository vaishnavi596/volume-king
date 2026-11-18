"""V2 static whole-feature migration preflight; old src read-only."""
import ast
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
OLD=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
NEW=(ROOT/"pilot_v2"/"android_app"/"src"/"main.py").read_text(encoding="utf-8")
FUNCTIONS={n.name:n for n in ast.walk(ast.parse(OLD)) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
GROUPS={
 "dashboard":("dashboard","dashboard_market_indices","dashboard_index_analysis","super_five_card"),
 "watchlist":("watchlist","watch_visible_tick","watch_three_minute_signal","refresh_watch_batch"),
 "scanner":("scanner","scanner_content","scanner_compact_chart","run_scan","choose_timeframe"),
 "super_five":("super_five_minute_refresh","publish_partial_ranking","five_engine_summary"),
 "options":("options","option_chain_preview","option_metrics","refresh_selected_options"),
 "settings":("settings","data_overview","render_page","refresh_after_resume"),
 "paper":("paper_trading_center","paper_tick","paper_bot_config_controls")
}
class GraphGate(unittest.TestCase):
 def test_all_real_handlers_exist(self):
  for group,names in GROUPS.items():
   with self.subTest(group=group):
    self.assertTrue(set(names).issubset(FUNCTIONS),str(set(names)-set(FUNCTIONS)))
 def test_dashboard_calls_real_engine_panels(self):
  calls={n.func.id for n in ast.walk(FUNCTIONS["dashboard"]) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
  for name in ("dashboard_market_indices","dashboard_index_analysis","super_five_card"):
   self.assertIn(name,calls)
 def test_scanner_calls_real_components(self):
  calls={n.func.id for n in ast.walk(FUNCTIONS["scanner_content"]) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
  for name in ("scanner_controls","safe_scanner_widget"):
   self.assertIn(name,calls)
  self.assertIn("ft.WebView(",OLD)
  self.assertIn("flet-webview",(ROOT/"pyproject.toml").read_text())
 def test_forbidden_old_feed_not_imported_by_v2_main(self):
  self.assertIn("from server_feed import ServerAngelFeed",OLD)
  self.assertIn("def get_yahoo(",OLD)
  self.assertNotIn("from server_feed import",NEW)
  self.assertNotIn("from market_feed import",NEW)
  self.assertNotIn("get_yahoo(",NEW)
  self.assertIn("from evidence_inbox import DeviceEvidenceInbox",NEW)
if __name__=="__main__":unittest.main()
