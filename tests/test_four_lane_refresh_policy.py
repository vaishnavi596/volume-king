"""Contract checks for logical four-lane read-only refresh scheduling.

Does not contact Oracle, Dhan or public RSS services.
"""
import ast
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from refresh_policy import (
    LANES, SUPER_FIVE_LOCAL_TICK_SECONDS, WATCHLIST_LOCAL_TICK_SECONDS,
    SCANNER_LOCAL_TICK_SECONDS, completed_bar_revision, data_changed,
)


class FourLanePolicyTests(unittest.TestCase):
    def test_exactly_four_nonoverlapping_logical_lanes(self):
        self.assertEqual(tuple(lane.name for lane in LANES),
                         ("quotes", "candles", "derivatives", "context"))
        consumers = [item for lane in LANES for item in lane.consumers]
        self.assertEqual(len(consumers), len(set(consumers)))
        self.assertGreaterEqual(len(consumers), 12)
        self.assertTrue(all(lane.requested_min_seconds >= 30 for lane in LANES))

    def test_local_display_checks_are_not_provider_requests(self):
        self.assertEqual(SUPER_FIVE_LOCAL_TICK_SECONDS, 2)
        self.assertEqual(WATCHLIST_LOCAL_TICK_SECONDS, 2)
        self.assertEqual(SCANNER_LOCAL_TICK_SECONDS, 2)
        self.assertFalse(data_changed(None, None))
        self.assertFalse(data_changed(("NIFTY", 1), ("NIFTY", 1)))
        self.assertTrue(data_changed(("NIFTY", 1), ("NIFTY", 2)))

    def test_completed_candle_revision_ignores_unrelated_quote_updates(self):
        rows = [[100, 10, 12, 9, 11, 100], [400, 11, 13, 10, 12, 90]]
        self.assertEqual(completed_bar_revision(rows), tuple(rows[-1]))
        self.assertEqual(completed_bar_revision([]), None)
        self.assertEqual(completed_bar_revision([[100, 10]]), None)

    def test_super_five_uses_pure_local_tick_and_shared_history(self):
        source = (ROOT / "src" / "main.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        methods = [node for node in ast.walk(tree)
                   if isinstance(node, ast.AsyncFunctionDef)
                   and node.name == "super_five_minute_refresh"]
        self.assertEqual(len(methods), 1)
        section = ast.get_source_segment(source, methods[0])
        self.assertIn("await asyncio.sleep(SUPER_FIVE_LOCAL_TICK_SECONDS)", section)
        self.assertIn("shared_history(sym)", section)
        self.assertIn("tuple(sorted(filter_modes.items()))", section)
        self.assertIn('prefs.get("confidence",75)', section)
        self.assertNotIn("dhan_feed.intraday(", section)
        self.assertNotIn("dhan_feed.batch_quotes(", section)


if __name__ == "__main__":
    unittest.main()
