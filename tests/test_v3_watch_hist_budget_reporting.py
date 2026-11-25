"""Watchlist 3/51 quota-exhaustion must explain pacing, not imply permanent hang."""
import ast
from pathlib import Path
import unittest
S=(Path(__file__).resolve().parents[1]/"src/main.py").read_text()
T=ast.parse(S)
def fn(name):
    x=[n for n in ast.walk(T) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
    assert len(x)==1,(name,len(x))
    return ast.get_source_segment(S,x[0])
class WatchHistoryBudgetUX(unittest.TestCase):
    def test_quota_wait_uses_actual_time_and_floor(self):
        body=fn("watch_hist_budget_wait_seconds")
        self.assertIn("time.monotonic()",body)
        self.assertIn("len(recent)>=12",body)
        self.assertIn("180-(now-min(recent))",body)
        self.assertIn("watch_three_minute_warm_last_provider[0]",body)
    def test_queue_wait_is_reported_without_new_provider_requests(self):
        body=fn("continue_closed_watch_history")
        self.assertIn("wait=watch_hist_budget_wait_seconds()",body)
        self.assertIn("provider pacing; next eligible",body)
        self.assertIn("waiting for worker or cooldown",body)
        self.assertIn("await asyncio.sleep(10)",body)
    def test_doctor_can_distinguish_active_paused_and_throttled(self):
        for value in ('"closed_hist_queue_active"','"closed_hist_resume_pending"',
                      '"closed_hist_pacing_wait_seconds"'):
            self.assertIn(value,S)
    def test_explicit_holiday_manual_only_retained(self):
        self.assertIn("explicit_closed=True",fn("continue_closed_watch_history"))
        self.assertIn("page.run_task(continue_closed_watch_history",fn("refresh_all_dhan_quotes"))
if __name__=="__main__":unittest.main()
