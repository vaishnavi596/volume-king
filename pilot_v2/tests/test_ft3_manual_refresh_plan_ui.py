"""V2 manual app refresh plan wired to existing intent, no provider traffic."""
from pathlib import Path
import ast
import sys
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

SRC=Path(__file__).resolve().parents[1]/"android_app"/"src"
sys.path.insert(0,str(SRC))
from app_state import LocalWatchlists
from smart_data import SmartDataSettings
from refresh_intent import make_refresh_intent

class ManualRefreshPlanTests(unittest.TestCase):
    def test_manual_request_selected_demand_only(self):
        for n in (0, 5, 51, 70):
            store=LocalWatchlists()
            for i in range(n):
                store.add(i % 5, f"EQ{i:03d}")
            intent=make_refresh_intent(
                store, SmartDataSettings(),
                datetime(2026,11,19,18,0,tzinfo=ZoneInfo("Asia/Kolkata")),
                manual=True, confirmed_session=False)
            self.assertEqual(len(intent.equities),n)
            self.assertEqual(intent.indexes,("NIFTY","BANKNIFTY","SENSEX"))
            self.assertEqual(intent.reason,"MANUAL_DATA_REQUEST_ONLY")

    def test_ui_callback_is_offline_preview(self):
        source=(SRC/"main.py").read_text(encoding="utf-8")
        tree=ast.parse(source)
        functions=[node for node in ast.walk(tree)
                   if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))
                   and node.name=="preview_manual_refresh"]
        self.assertEqual(len(functions),1)
        callback=functions[0]
        calls=[node.func.id for node in ast.walk(callback)
               if isinstance(node,ast.Call) and isinstance(node.func,ast.Name)]
        self.assertIn("make_refresh_intent",calls)
        self.assertIn("render",calls)
        self.assertNotIn("request",calls)
        self.assertNotIn("get",calls)
        self.assertIn('on_click=preview_manual_refresh',source)
        self.assertIn('no fetch',source)
        self.assertNotIn("ServerAngelFeed",source)
        self.assertNotIn("get_yahoo(",source)

if __name__=="__main__":
    unittest.main()
