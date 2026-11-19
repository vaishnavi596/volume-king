"""Local V2 in-app notices never become market or broker alerts."""
import ast
import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from local_notices import LocalNoticeCenter, LocalNoticeError, MAX_NOTICES


class LocalNoticeTests(unittest.TestCase):
    def test_only_allowlisted_app_events_and_bounded_session_history(self):
        notices = LocalNoticeCenter()
        for event in ("WATCHLIST_ADDED", "WATCHLIST_REMOVED",
                      "PAPER_PLAN_SAVED", "PAPER_PLAN_CLEARED",
                      "LOCAL_PREFS_RESTORED"):
            notices.record(event)
        self.assertEqual(notices.unread, 5)
        self.assertEqual(len(notices.visible()), 5)
        for event in ("BUY", "SELL", "NIFTY up", "Dhan token:secret", "", None):
            with self.subTest(event=event), self.assertRaises(LocalNoticeError):
                notices.record(event)
        notices.mark_read()
        self.assertEqual(notices.unread, 0)
        for _ in range(MAX_NOTICES + 7):
            notices.record("WATCHLIST_ADDED")
        self.assertEqual(len(notices.visible()), MAX_NOTICES)
        self.assertEqual(notices.unread, MAX_NOTICES)
        notices.clear()
        self.assertEqual(notices.visible(), ())
        self.assertEqual(notices.unread, 0)

    def test_flet_events_and_settings_notice_center_are_connected(self):
        src = (SRC / "main.py").read_text(encoding="utf-8")
        ast.parse(src)
        for marker in ('from local_notices import LocalNoticeCenter',
                       'notices = LocalNoticeCenter()',
                       'notices.record("WATCHLIST_ADDED")',
                       'notices.record("WATCHLIST_REMOVED")',
                       'notices.record("PAPER_PLAN_SAVED")',
                       'notices.record("PAPER_PLAN_CLEARED")',
                       'notices.record("LOCAL_PREFS_RESTORED")',
                       'ft.Text("Local notices · session only"',
                       "notices.mark_read()",
                       "notices.clear()"):
            self.assertIn(marker, src)
        self.assertEqual(src.count('ft.NavigationDestination('), 3)
        for bad in ("submit_order(", "place_order(", "get_yahoo(", "ServerAngelFeed("):
            self.assertNotIn(bad, src)

    def test_module_does_not_import_network_or_broker(self):
        code = (SRC / "local_notices.py").read_text()
        tree = ast.parse(code)
        self.assertFalse([n for n in ast.walk(tree)
                          if isinstance(n, (ast.Import, ast.ImportFrom))])


if __name__ == "__main__":
    unittest.main()
