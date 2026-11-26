"""One Watchlist tap starts a bounded, cancellable SSK historical queue."""
import ast
import pathlib
import unittest

SOURCE=(pathlib.Path(__file__).resolve().parents[1]/"src"/"main.py").read_text()
TREE=ast.parse(SOURCE)
def function(name):
    found=[n for n in ast.walk(TREE) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
    assert len(found)==1,(name,len(found))
    return ast.get_source_segment(SOURCE,found[0])

class ClosedHistoricalQueueContract(unittest.TestCase):
    def test_manual_one_tap_queues_a_single_worker_without_live_quote(self):
        src=function("refresh_all_dhan_quotes")
        self.assertIn('watch_closed_hist_loading[0]=True',src)
        self.assertIn('page.run_task(continue_closed_watch_history',src)
        self.assertIn('if not watch_closed_hist_loading[0]',src)
        self.assertLess(src.index('if closed_ssk_hist:'),src.index('if not dhan_feed.connected:'))
        self.assertIn('and not dhan_feed.connected',src)

    def test_auto_queue_respects_foreground_auth_generation_scope(self):
        src=function("continue_closed_watch_history")
        for guard in ('provider_generation[0]!=generation',
                      'active_watch[0]!=list_index',
                      '(search.value or "").upper()!=search_scope',
                      'not app_active[0]', 'lifecycle_background[0]',
                      'not clone_v2_gateway.connected', 'refresh_hours()',
                      'prefs.get("source")!="Dhan"'):
            self.assertIn(guard,src)
        self.assertIn('await warm_selected_watch_three_minute_early(',src)
        self.assertIn('explicit_closed=True',src)
        self.assertIn('await asyncio.sleep(10)',src)
        self.assertIn('watch_closed_hist_loading[0]=False',src)
        self.assertNotIn('refresh_watch_batch(',src)

    def test_explicit_queue_can_continue_across_foreground_tabs(self):
        queue=function("continue_closed_watch_history")
        self.assertNotIn("or current[0]!=4",queue)
        warm=function("warm_selected_watch_three_minute_early")
        self.assertNotIn("current[0]!=4",warm)
        self.assertIn("generation!=provider_generation[0]",warm)
        self.assertIn("not refresh_hours() and not explicit_closed",warm)
        self.assertIn("explicit_closed and scope!=",warm)
        self.assertIn("not app_active[0] or lifecycle_background[0]",warm)

    def test_closed_queue_has_one_bounded_retry_pass(self):
        queue=function("continue_closed_watch_history")
        self.assertIn("attempted and not retry_pass",queue)
        self.assertIn("retry_pass=True",queue)
        self.assertIn("closed_retry_baseline=retry_baseline if retry_pass else None",queue)
        warm=function("warm_selected_watch_three_minute_early")
        self.assertIn("watch_three_minute_warm_attempts[key]>closed_retry_baseline[sym]",warm)
        self.assertNotIn("watch_three_minute_warm_attempts.get(key,0)",warm)
        self.assertIn("now-watch_three_minute_warm_attempts[key]<180",warm)

    def test_pacing_budget_not_bypassed(self):
        src=function("warm_selected_watch_three_minute_early")
        self.assertIn('len(watch_three_minute_upstream_times)>=(40 if explicit_closed else 12)',src)
        self.assertIn('now-watch_three_minute_warm_last_provider[0]<(3 if explicit_closed else 10)',src)
        self.assertIn('get_market_data,sym,"1m","2d"',src)
        self.assertIn('return False  # At most one selected equity per 5m scan cycle.',src)

    def test_unavailable_symbols_are_not_claimed_as_completed(self):
        src=function("continue_closed_watch_history")
        self.assertIn('if attempted else f"HIST complete {finished}/{total}',src)
        self.assertIn('HIST loaded {finished}/{total} • unavailable after attempt',src)

    def test_button_disables_while_worker_running(self):
        src=function("watchlist")
        self.assertIn('or watch_closed_hist_loading[0]',src)
        tick=function("watch_visible_tick")
        self.assertIn('or watch_closed_hist_loading[0]',tick)

if __name__=="__main__":
    unittest.main()
