"""Regression guards for mobile v2.3.127 lost-candles / Super Five incident.

These structural checks complement isolated candle_retention behavioral tests.
They intentionally do not call a broker or label historical results LIVE.
"""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "src" / "main.py"


def method_source(name):
    text = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(text)
    matches = [node for node in ast.walk(tree)
               if isinstance(node, ast.AsyncFunctionDef) and node.name == name]
    assert len(matches) == 1, (name, len(matches))
    return ast.get_source_segment(text, matches[0])


class MobileHistoryContinuity(unittest.TestCase):
    def test_super_five_reuses_valid_shared_history_without_upstream_calls(self):
        source = method_source("super_five_minute_refresh")
        self.assertIn("shared_history(sym)", source)
        self.assertIn("valid_candle_history(bars)", source)
        self.assertIn("retain_last_filter_votes(", source)
        self.assertNotIn("get_market_data(", source)
        self.assertNotIn("dhan_feed.intraday(", source)
        self.assertNotIn("dhan_feed.batch_quotes(", source)

    def test_disconnected_cached_history_still_can_recompute_as_historical(self):
        source = method_source("super_five_minute_refresh")
        self.assertNotIn('and not dhan_feed.connected', source)
        self.assertIn("not app_active[0]", source)

    def test_index_candle_poll_rejects_short_or_older_before_replacement(self):
        source = method_source("dhan_index_candle_poll")
        self.assertIn("retain_candle_history(data,prior", source)
        self.assertIn('valid_candle_history(data.get("bars"))', source)
        self.assertIn('refresh_shared_analysis(index_sym)', source)
        self.assertIn('cooldown_remaining("/dhan/intraday")', source)


if __name__ == "__main__":
    unittest.main()
