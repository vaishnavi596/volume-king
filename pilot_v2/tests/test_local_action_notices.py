"""Complete local-only V2 action notice parity without market/broker alerts."""
import ast
import sys
import unittest
from pathlib import Path
SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from local_notices import LocalNoticeCenter, LocalNoticeError, EVENTS, MAX_NOTICES

class LocalActionNoticeParity(unittest.TestCase):
    def test_whitelisted_paper_simulation_and_chart_controls(self):
        center = LocalNoticeCenter()
        for code in ("PAPER_SIM_OPENED", "PAPER_SIM_CLOSED",
                     "CHART_STYLE_CHANGED"):
            self.assertIn(code, EVENTS)
            center.record(code)
        self.assertEqual(center.unread, 3)
        messages = center.visible()
        self.assertEqual(len(messages), 3)
        self.assertTrue(all("locally" in text for text, _ in messages))
        center.mark_read()
        self.assertEqual(center.unread, 0)
        for _ in range(MAX_NOTICES + 2):
            center.record("CHART_STYLE_CHANGED")
        self.assertEqual(len(center.visible()), MAX_NOTICES)

    def test_untrusted_market_events_or_free_text_are_never_accepted(self):
        center = LocalNoticeCenter()
        for code in ("BUY", "SELL", "PRICE_TARGET",
                     "NIFTY bullish", "Dhan token abc", "", None, 7):
            with self.subTest(code=code), self.assertRaises(LocalNoticeError):
                center.record(code)
        self.assertEqual(center.visible(), ())

    def test_real_ui_records_only_after_action_succeeds(self):
        src = (SRC / "main.py").read_text(encoding="utf-8")
        ast.parse(src)
        for code, after in (
            ("PAPER_SIM_OPENED", "ledger.open_simulation("),
            ("PAPER_SIM_CLOSED", "ledger.close_simulation("),
            ("CHART_STYLE_CHANGED", "chart_style[0] = chart_style_choice("),
        ):
            index = src.index('notices.record("' + code + '")')
            self.assertIn(after, src[index - 260:index])
        self.assertNotIn("submit_order(", src)
        self.assertNotIn("get_yahoo(", src)
        self.assertEqual(src.count("ft.NavigationDestination("), 3)

if __name__ == "__main__":
    unittest.main()
