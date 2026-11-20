"""Regression: late Watchlist entry receives bounded 3m assessment reads."""
import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "src" / "main.py").read_text(encoding="utf-8")


class WatchAssessmentRecovery(unittest.TestCase):
    def test_main_parses(self):
        ast.parse(SOURCE)

    def test_closed_watch_recovery_bounded_per_generation(self):
        self.assertIn("oracle_assessment_closed_watch_attempts={}", SOURCE)
        self.assertIn("len(oracle_assessment_closed_watch_attempts.get(generation,set()))>=3", SOURCE)
        self.assertIn('if not market_window and current[0]==4 and tf=="3m":', SOURCE)
        self.assertIn("if sym in tried or len(tried)>=3:", SOURCE)
        self.assertIn("tried.add(sym)", SOURCE)

    def test_no_other_lane_recovery_and_no_broker_fanout(self):
        self.assertIn("elif not market_window and bootstrap_done:", SOURCE)
        self.assertIn("Late Watchlist recovery cannot poll other lanes.", SOURCE)
        self.assertIn("dhan_feed.assessment,sym,timeframe=tf,expiry=selected_expiry", SOURCE)
        self.assertIn("oracle_assessment_attempts[key]=now", SOURCE)

    def test_existing_two_second_watch_tick_and_quote_clock(self):
        self.assertIn("async def watch_visible_tick():", SOURCE)
        self.assertIn("await asyncio.sleep(2)", SOURCE)
        self.assertIn("async def dhan_quote_poll():", SOURCE)
        self.assertIn("watch_batch_last_attempt[0])>=60", SOURCE)


if __name__ == "__main__":
    unittest.main()
