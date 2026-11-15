"""Watchlist timer must not recreate the 51-row view every countdown tick."""
from pathlib import Path
import unittest


class WatchCountdownIncrementalTests(unittest.TestCase):
    def test_countdown_updates_its_own_mounted_control(self):
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        start=source.index("    async def watch_visible_tick():")
        end=source.index("    def watchlist():",start)
        worker=source[start:end]
        countdown=worker[worker.index("if watch_countdown.value!=label:"):worker.index("visible=tuple(")]
        self.assertIn("watch_countdown.update()",countdown)
        self.assertNotIn("request_view_refresh(4)",countdown)
        self.assertIn("if watch_countdown.page is not None:",countdown)
        self.assertIn("if signature!=last_visible_signature:",worker)
        self.assertIn("request_view_refresh(4)",worker)


    def test_countdown_uses_any_actual_batch_attempt_and_pauses_in_background(self):
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        start=source.index("    def next_watch_refresh_label():")
        end=source.index("    async def watch_visible_tick():",start)
        label_source=source[start:end]
        self.assertIn("watch_batch_last_attempt[0]",label_source)
        self.assertIn("quote_auto_last_attempt[0]",label_source)
        self.assertIn("last_attempt=max(",label_source)
        self.assertIn('return "Paused"',label_source)
        self.assertIn("if elapsed>=60:",label_source)

if __name__=="__main__":
    unittest.main()
