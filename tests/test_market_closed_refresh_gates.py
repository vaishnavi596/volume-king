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

    def test_closed_market_disables_auto_poll_but_manual_refresh_is_available(self):
        label=section("    def watchlist():","    symbol=ft.Dropdown(")
        self.assertIn('ft.TextButton("Refresh data"',label)
        self.assertNotIn("watch_countdown",label)
        manual=section("    async def refresh_all_dhan_quotes():","    quote_auto_last_attempt=")
        self.assertIn("await refresh_watch_batch()",manual)
        self.assertIn("await refresh_dhan_index_quotes(force=True)",manual)
        # The market-hours condition applies only to the extra explicit HIST
        # request, NEVER to the manual equity/index quote refresh itself.
        # The after-hours history branch is additionally blocked by the
        # selected-equity 429 cooldown, while quotes remain manually available.
        hist_gate='if cooldown==0 and not refresh_hours() and current[0]==4:'
        self.assertIn(hist_gate,manual)
        self.assertIn('if cooldown==0:',manual)
        self.assertIn('if index_cooldown==0:',manual)
        self.assertIn('if cooldown>0 and index_cooldown>0:',manual)
        self.assertLess(manual.index('if cooldown==0:'),
                        manual.index('await refresh_watch_batch()'))
        self.assertLess(manual.index('if index_cooldown==0:'),
                        manual.index('await refresh_dhan_index_quotes(force=True)'))
        self.assertLess(manual.index('await refresh_watch_batch()'),
                        manual.index('await refresh_dhan_index_quotes(force=True)'))
        self.assertLess(manual.index('await refresh_dhan_index_quotes(force=True)'),
                        manual.index(hist_gate))
        self.assertIn('warm_selected_watch_three_minute_early(',manual)
        self.assertIn('explicit_closed=True',manual)
        self.assertIn('if dhan_history_scan_active[0]:',manual)
        self.assertIn("max(0,30-",manual)

    def test_resume_checks_selected_route_cooldown_and_indices_remain_independent(self):
        resume=section("    async def refresh_after_resume():","    def lifecycle_changed(e):")
        self.assertIn('dhan_feed.cooldown_remaining("/v2/snapshot")==0',resume)
        self.assertIn('dhan_feed.cooldown_remaining("/dhan/selected-ltp-batch")==0',resume)
        self.assertLess(resume.index('dhan_feed.cooldown_remaining("/dhan/selected-ltp-batch")==0'),
                        resume.index("await refresh_watch_batch()"))
        self.assertLess(resume.index("await refresh_watch_batch()"),
                        resume.index("await refresh_dhan_index_quotes()"))
        index=section("    async def refresh_dhan_index_quotes(force=False):","    manual_quote_last_attempt=")
        self.assertIn('index_cooldown=dhan_feed.cooldown_remaining("/dhan/index-ltp-batch")',index)
        self.assertIn("if index_cooldown>0:",index)
        self.assertIn('login_bootstrap.finish(provider_generation[0],"indices",0,3,error="cooldown")',index)
        self.assertLess(index.index("if index_cooldown>0:"),
                        index.index("snapshots=await asyncio.to_thread(dhan_feed.index_batch_quotes)"))

    def test_smart_quote_clock_is_safely_bounded_and_view_focused(self):
        from clone_smart_refresh_priority import auto_equity_quote_due, active_quote_view
        self.assertTrue(auto_equity_quote_due(100, 0))
        self.assertFalse(auto_equity_quote_due(159, 100))
        self.assertTrue(auto_equity_quote_due(160, 100))
        self.assertFalse(auto_equity_quote_due(170, 171))
        self.assertFalse(auto_equity_quote_due(999, 100, busy=True))
        self.assertFalse(auto_equity_quote_due(110, 100, floor_seconds=2))
        self.assertEqual([active_quote_view(p) for p in range(6)],
                         [0,None,None,3,4,None])
        poll=section("    async def dhan_quote_poll():","    # The Watchlist observes")
        self.assertIn("auto_equity_quote_due(",poll)
        self.assertIn('dhan_feed.cooldown_remaining("/dhan/selected-ltp-batch")',poll)
        batch=section("    async def refresh_watch_batch():","    index_refresh_busy=[False]")
        self.assertIn("active_quote_view(current[0])",batch)
        self.assertIn("request_view_refresh(visible_target)",batch)

    def test_super_five_local_loop_reuses_candles_after_close_without_network(self):
        loop=section("    async def super_five_minute_refresh():","    def five_engine_summary(symbol, display_timeframe=None):")
        self.assertNotIn("not refresh_hours()",loop)
        self.assertIn('bars=data.get("bars") or []',loop)
        self.assertIn("await local_analysis_pool.run(display_analysis,sym,snapshot,frozen=frozen)",loop)
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
