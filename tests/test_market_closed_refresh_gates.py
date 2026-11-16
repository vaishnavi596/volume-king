"""Closed-session automatic market-data requests must stop without hiding cached quotes."""
import unittest
from pathlib import Path

SOURCE=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")


def section(start,end):
    return SOURCE.split(start,1)[1].split(end,1)[0]


class ClosedSessionRefreshGates(unittest.TestCase):
    def test_equity_and_index_poll_require_open_session(self):
        self.assertIn("app_active[0] and refresh_hours()", section("    async def dhan_quote_poll():","    # The Watchlist observes"))
        self.assertIn("app_active[0] and refresh_hours()", section("    async def dhan_index_poll():","    page.run_task(dhan_index_poll)"))

    def test_page_entry_and_resume_reuse_cached_closed_data(self):
        self.assertIn("changed and i==4 and refresh_hours()",section("    def render_page(i):","    # Keep the app chrome inside Android system insets"))
        resume=section("    async def refresh_after_resume():","    def lifecycle_changed(e):")
        self.assertIn("if not refresh_hours():",resume)
        self.assertIn("saved data retained",resume)

    def test_closed_market_disables_auto_poll_but_manual_refresh_is_available():
        label=section("    def watchlist():","    symbol=ft.Dropdown(")
        self.assertIn('ft.TextButton("Refresh data"',label)
        self.assertNotIn("watch_countdown",label)
        manual=section("    async def refresh_all_dhan_quotes():","    quote_auto_last_attempt=")
        self.assertIn("await refresh_watch_batch()",manual)
        self.assertIn("await refresh_dhan_index_quotes(force=True)",manual)
        self.assertNotIn("refresh_hours()",manual)
        self.assertIn("max(0,30-",manual)

    def test_super_five_local_loop_reuses_candles_after_close_without_network(self):
        loop=section("    async def super_five_minute_refresh():","    def five_engine_summary(symbol):")
        self.assertNotIn("not refresh_hours()",loop)
        self.assertIn('bars=snapshot.get("bars") or []',loop)
        self.assertIn("fingerprint==last_fingerprint",loop)
        self.assertIn("publish_partial_ranking(results)",loop)
        self.assertNotIn("dhan_feed.batch_quotes",loop)
        self.assertNotIn("dhan_feed.option_chain_metrics",loop)

    def test_index_force_is_explicit_bypass_only(self):
        index=section("    async def refresh_dhan_index_quotes(force=False):","    manual_quote_last_attempt=")
        self.assertIn("if not force and not refresh_hours():",index)
        self.assertIn("old=quotes.get(ticker)",index)

if __name__=="__main__":
    unittest.main()
