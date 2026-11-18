"""Synthetic V2 local Smart Data policy, no timer, Dhan request or Flet dependency."""
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import importlib.util
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1] / "android_app" / "src"
def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + ".py"))
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m

smart = load("smart_data")
watch = load("app_state")
IST = ZoneInfo("Asia/Kolkata")

class AppSmartDataTests(unittest.TestCase):
    def test_five_symbols_means_five_not_seventy_and_indexes_independent(self):
        for n in (0, 5, 51, 70):
            with self.subTest(n=n):
                lists = watch.LocalWatchlists()
                for i in range(n):
                    lists.add(i % 5, f"EQ{i:03d}")
                plan = smart.selected_equity_plan(lists)
                self.assertEqual(plan["equity_count"], n)
                self.assertEqual(len(plan["equities"]), n)
                self.assertEqual(plan["indices"], watch.INDEXES)

    def test_refresh_window_and_market_confirmation(self):
        cfg = smart.SmartDataSettings()
        date = (2026, 11, 18)
        def tick(hour, minute):
            return datetime(*date, hour, minute, tzinfo=IST)
        self.assertFalse(smart.permitted_auto_refresh(tick(9, 9),market_session_confirmed=True,settings=cfg))
        self.assertTrue(smart.permitted_auto_refresh(tick(9, 10),market_session_confirmed=True,settings=cfg))
        self.assertTrue(smart.permitted_auto_refresh(tick(15, 45),market_session_confirmed=True,settings=cfg))
        self.assertFalse(smart.permitted_auto_refresh(tick(15, 46),market_session_confirmed=True,settings=cfg))
        self.assertFalse(smart.permitted_auto_refresh(tick(10, 0),market_session_confirmed=False,settings=cfg))
        self.assertFalse(smart.permitted_auto_refresh(tick(10, 0),market_session_confirmed=True,
                         settings=smart.SmartDataSettings(False,180)))
        self.assertFalse(smart.permitted_auto_refresh(datetime(2026,11,21,10,0,tzinfo=IST),
                         market_session_confirmed=True,settings=cfg))
        with self.assertRaises(smart.SmartDataError):
            smart.permitted_auto_refresh(datetime(2026,11,18,10,0),market_session_confirmed=True,settings=cfg)

    def test_saved_settings_schema_and_strict_types(self):
        cfg = smart.SmartDataSettings(False, 300)
        self.assertEqual(smart.SmartDataSettings.from_saved(cfg.saved_state()), cfg)
        for bad in (None, {}, {"schema_version":True,"auto_refresh":True,"equity_seconds":180},
                    {"schema_version":1,"auto_refresh":1,"equity_seconds":180},
                    {"schema_version":1,"auto_refresh":True,"equity_seconds":30},
                    {"schema_version":1,"auto_refresh":True,"equity_seconds":True},
                    dict(cfg.saved_state(), secret="no")):
            with self.subTest(bad=repr(bad)), self.assertRaises(smart.SmartDataError):
                smart.SmartDataSettings.from_saved(bad)

if __name__ == "__main__":
    unittest.main()
