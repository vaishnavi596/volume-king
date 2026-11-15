"""Closed-session automatic market-data requests must stop without hiding cached quotes."""
import unittest
from pathlib import Path

SOURCE=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")


def section(start,end):
    return SOURCE.split(start,1)[1].split(end,1)[0]


class ClosedSessionRefreshGates(unittest.TestCase):
    def test_equity_and_index_poll_require_open_session(self):
        self.assertIn("app_active[0] and regular_hours()", section("    async def dhan_quote_poll():","    # Compact countdown updates independently"))
        self.assertIn("app_active[0] and regular_hours()", section("    async def dhan_index_poll():","    page.run_task(dhan_index_poll)"))

    def test_page_entry_and_resume_reuse_cached_closed_data(self):
        self.assertIn("changed and i==4 and regular_hours()",section("    def render_page(i):","    # Keep the app chrome inside Android system insets"))
        resume=section("    async def refresh_after_resume():","    def lifecycle_changed(e):")
        self.assertIn("if not regular_hours():",resume)
        self.assertIn("saved data retained",resume)

    def test_watch_countdown_displays_pause_not_next_interval(self):
        label=section("    def next_watch_refresh_label():","    async def watch_visible_tick():")
        self.assertIn('return "Market closed • auto-refresh paused"',label)

    def test_super_five_local_loop_pauses_off_hours(self):
        loop=section("    async def super_five_minute_refresh():","    def five_engine_summary(symbol):")
        self.assertIn("not regular_hours()",loop)

    def test_index_force_is_explicit_bypass_only(self):
        index=section("    async def refresh_dhan_index_quotes(force=False):","    manual_quote_last_attempt=")
        self.assertIn("if not force and not regular_hours():",index)
        self.assertIn("old=quotes.get(ticker)",index)

if __name__=="__main__":
    unittest.main()
