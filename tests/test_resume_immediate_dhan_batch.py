"""Android resume should request a Dhan batch without waiting for poll tick."""
from pathlib import Path
import unittest
S=(Path(__file__).resolve().parents[1]/"src/main.py").read_text(encoding="utf-8")
RESUME=S.split("    async def refresh_after_resume():",1)[1].split("    def lifecycle_changed(e):",1)[0]
class ResumeBatchTests(unittest.TestCase):
    def test_resume_batch_precedes_candle_fetch(self):
        self.assertLess(RESUME.index("await refresh_watch_batch()"),RESUME.index("get_market_data,sym"))
    def test_requires_active_authenticated_dhan_and_no_cooldown(self):
        for token in ('app_active[0]','prefs.get("source")=="Dhan"',
                      'dhan_feed.connected','dhan_feed.cooldown_remaining("/v2/snapshot")==0'):
            self.assertIn(token,RESUME)
    def test_abort_after_background_or_provider_switch(self):
        self.assertIn("if not app_active[0] or generation!=provider_generation[0]:",RESUME)
    def test_background_poll_remains_suspended(self):
        poll=S.split("    async def dhan_quote_poll():",1)[1].split("    async def ",1)[0]
        self.assertIn('app_active[0] and prefs.get("source")=="Dhan"',poll)
if __name__=="__main__":
    unittest.main()
