"""User-started closed-session historical queue resumes on foreground Watchlist return.

This is a source contract: no unsolicited holiday auto-history polling.
"""
import ast
from pathlib import Path
import unittest

SOURCE=(Path(__file__).resolve().parents[1]/"src/main.py").read_text(encoding="utf-8")
TREE=ast.parse(SOURCE)

def body(name):
    matches=[n for n in ast.walk(TREE) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
    assert len(matches)==1,(name,len(matches))
    return ast.get_source_segment(SOURCE,matches[0])

class ClosedWatchResumeContract(unittest.TestCase):
    def test_queue_resume_requires_prior_user_request_and_foreground_watchlist(self):
        helper=body("resume_interrupted_closed_watch_history")
        for guard in ("watch_closed_hist_resume_pending[0]","not watch_closed_hist_loading[0]",
                      "current[0]==4","app_active[0]","not lifecycle_background[0]",
                      "clone_v2_gateway.connected","not refresh_hours()"):
            self.assertIn(guard,helper)
        self.assertIn("await refresh_all_dhan_quotes()",helper)
    def test_manual_only_start_and_pause(self):
        manual=body("refresh_all_dhan_quotes")
        queue=body("continue_closed_watch_history")
        self.assertIn("page.run_task(continue_closed_watch_history",manual)
        self.assertIn("watch_closed_hist_resume_pending[0]=False",manual)
        self.assertIn("watch_closed_hist_resume_pending[0]=bool(",queue)
        self.assertIn("HIST paused • resumes on Watchlist return",queue)
    def test_navigation_and_resume_hook(self):
        self.assertIn("if changed and i==4 and watch_closed_hist_resume_pending[0]:",body("render_page"))
        self.assertIn("if current[0]==4 and watch_closed_hist_resume_pending[0]:",body("lifecycle_changed"))
    def test_no_unsolicited_closed_session_auto_scan(self):
        self.assertIn("if not initial and not refresh_hours()",body("refresh_market"))
        self.assertIn("if not refresh_hours():",body("refresh_after_resume"))

if __name__=="__main__":
    unittest.main()
