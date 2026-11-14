"""Offline regression guards for independent BOT KING watchlist refresh."""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "src" / "main.py"


class WatchlistRefreshRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_python_syntax(self):
        ast.parse(self.source, filename=str(SOURCE))

    def test_quote_poll_uses_connection_aware_interval(self):
        tree = ast.parse(self.source)
        poll = next(node for node in ast.walk(tree)
                    if isinstance(node, ast.AsyncFunctionDef)
                    and node.name == "dhan_quote_poll")
        sleeps = [node for node in ast.walk(poll)
                  if isinstance(node, ast.Call)
                  and isinstance(node.func, ast.Attribute)
                  and node.func.attr == "sleep"]
        self.assertTrue(any(call.args and isinstance(call.args[0], ast.IfExp)
                            and isinstance(call.args[0].body, ast.Constant)
                            and call.args[0].body.value == 10
                            and isinstance(call.args[0].orelse, ast.Constant)
                            and call.args[0].orelse.value == 10 for call in sleeps))

    def test_no_scroll_triggered_quote_requests(self):
        self.assertNotIn("watch_list.on_scroll=", self.source)
        self.assertNotIn("refresh_watch_on_scroll", self.source)

    def test_historical_votes_explicitly_not_live(self):
        self.assertIn("Historical votes (NOT live signal)", self.source)
        self.assertIn("bull_bar_color=GREEN", self.source)
        self.assertIn("bear_bar_color=RED", self.source)

    def test_change_aware_watchlist_refresh(self):
        self.assertIn("if signature!=last_visible_signature:", self.source)
        self.assertIn("await asyncio.sleep(2)", self.source)


if __name__ == "__main__":
    unittest.main()
