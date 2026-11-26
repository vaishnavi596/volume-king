"""B205 phone: exact SSK-only manual Watchlist HIST button and compact closed engine chips."""
import ast
import pathlib
import unittest

SOURCE=(pathlib.Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
TREE=ast.parse(SOURCE)
def body(name):
    matches=[x for x in ast.walk(TREE) if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))
             and x.name==name]
    assert len(matches)==1,(name,len(matches))
    return ast.get_source_segment(SOURCE,matches[0])
class B205PhoneSSKWatchlist(unittest.TestCase):
    def test_explicit_ssk_history_before_live_only_gate(self):
        s=body("refresh_all_dhan_quotes")
        self.assertIn('closed_ssk_hist=(clone_v2_gateway.connected and not refresh_hours()',s)
        self.assertIn('and not dhan_feed.connected)',s)
        self.assertIn('provider_generation[0],explicit_closed=True)',s)
        self.assertLess(s.index('if closed_ssk_hist:'),s.index('if not dhan_feed.connected:'))
        self.assertLess(s.index('if closed_ssk_hist:'),s.index('await refresh_watch_batch()'))
    def test_ssk_auth_source_budget_and_no_auto_holiday_request(self):
        s=body("warm_selected_watch_three_minute_early")
        for q in ('explicit_closed and clone_v2_gateway.connected and not refresh_hours()',
                  'explicit_closed and refresh_hours()',
                  'not clone_v2_gateway.connected',
                  'len(watch_three_minute_upstream_times)>=(40 if explicit_closed else 12)',
                  'now-watch_three_minute_warm_last_provider[0]<(3 if explicit_closed else 10)',
                  'get_market_data,sym,"1m","2d"'):
            self.assertIn(q,s)
    def test_watchlist_button_and_mounted_tick_allow_ssk(self):
        self.assertIn('clone_v2_gateway.connected and not refresh_hours()',body("watchlist"))
        self.assertIn('clone_v2_gateway.connected and not refresh_hours()',body("watch_visible_tick"))
    def test_compact_closed_boxes_and_true_hist_preserved(self):
        s=body("five_engine_chips")
        self.assertIn('label=short+" WAIT"',s)
        self.assertNotIn('label=short+" OFF"',s)
        self.assertIn('historical=True',s)
if __name__=="__main__": unittest.main()
