"""Watchlist timer must not recreate the 51-row view every countdown tick."""
from pathlib import Path
import unittest


class WatchCountdownIncrementalTests(unittest.TestCase):
    def test_visible_tick_updates_only_on_quote_or_filter_changes(self):
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        worker=source.split("    async def watch_visible_tick():",1)[1].split("    def watchlist():",1)[0]
        self.assertIn("await asyncio.sleep(2)",worker)
        self.assertIn("if signature!=last_visible_signature:",worker)
        self.assertIn("request_view_refresh(4)",worker)
        self.assertIn('watch_signal_cache.get(sym)',worker)
        self.assertNotIn("watch_countdown.update()",worker)
        self.assertNotIn("Next due",worker)

    def test_watchlist_has_one_prominent_manual_refresh_and_no_countdown(self):
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        watch=source.split("    def watchlist():",1)[1].split("    symbol=ft.Dropdown(",1)[0]
        self.assertIn('ft.TextButton("Refresh data"',watch)
        self.assertIn("page.run_task(refresh_all_dhan_quotes)",watch)
        self.assertNotIn("watch_countdown",watch)
        self.assertNotIn("Refresh Dhan LTP",watch)
        self.assertNotIn("LTP • every 60 sec",watch)

    def test_watchlist_navigation_and_poll_share_request_clock(self):
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        poll=source.split("    async def dhan_quote_poll():",1)[1].split("    # Compact countdown updates independently",1)[0]
        render=source.split("    def render_page(i):",1)[1].split("    # Keep the app chrome inside Android system insets",1)[0]
        self.assertIn("max(quote_auto_last_attempt[0],watch_batch_last_attempt[0])>=60",poll)
        self.assertNotIn("quote_auto_last_attempt[0]=time.monotonic()",poll)
        self.assertIn("time.monotonic()-watch_batch_last_attempt[0]>=60",render)
        self.assertIn('dhan_feed.cooldown_remaining("/v2/snapshot")==0',render)
        self.assertIn("not watch_batch_busy[0]",render)
        self.assertIn("await refresh_watch_batch()",poll)

    def test_resume_does_not_duplicate_recent_snapshot(self):
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        body=source.split("    async def refresh_after_resume():",1)[1].split("    def lifecycle_changed(e):",1)[0]
        self.assertIn("max(quote_auto_last_attempt[0],watch_batch_last_attempt[0])>=60",body)
        self.assertNotIn("quote_auto_last_attempt[0]=time.monotonic()",body)
        self.assertIn("await refresh_watch_batch()",body)

    def test_super_five_reuses_cache_and_skips_unmodified_candles(self):
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        body=source.split("    async def super_five_minute_refresh():",1)[1].split("    def five_engine_summary(symbol):",1)[0]
        self.assertIn("await asyncio.sleep(10)",body)
        self.assertIn("fingerprint==last_fingerprint",body)
        self.assertIn("tuple(filter_selected)",body)
        self.assertIn("publish_partial_ranking(results)",body)
        self.assertNotIn("dhan_feed.batch_quotes",body)
        self.assertNotIn("get_market_data(",body)

    def test_login_batch_starts_shared_request_clock(self):
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        login=source.split("                    # Verify watchlist batch independently of the login check.",1)[1].split("                    if market_status.startswith",1)[0]
        self.assertIn("watch_batch_last_attempt[0]=time.monotonic()",login)
        self.assertIn("batch=await asyncio.to_thread(dhan_feed.equity_quotes_with_bootstrap)",login)

if __name__=="__main__":
    unittest.main()
