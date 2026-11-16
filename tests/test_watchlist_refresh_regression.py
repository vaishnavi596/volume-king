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
        self.assertIn("HIST • NOT live", self.source)
        self.assertIn("bgcolor=GREEN,expand=bull", self.source)
        self.assertIn("bgcolor=RED,expand=bear", self.source)

    def test_change_aware_watchlist_refresh(self):
        self.assertIn("if signature==last_visible_signature", self.source)
        self.assertIn("await asyncio.sleep(2)", self.source)
        self.assertIn("if target==4 and current[0]==4 and watch_list.page is not None:", self.source)
        self.assertIn("watch_row_cells[sym]=", self.source)

    def test_price_and_filter_cells_have_mounted_identity(self):
        body=self.source.split("    def fill_watch(_=None):",1)[1].split("    search.on_change=fill_watch",1)[0]
        for name in ("price_cell","change_cell","five_cell","assessment_cell",
                     "signal_cell","freshness_cell"):
            self.assertIn(name+"=",body)
        self.assertIn("watch_row_cells[sym]=",body)
        self.assertIn("txt(sym,16,WHITE,True)",body)
        tick=self.source.split("    async def watch_visible_tick():",1)[1].split(
            "    def watchlist():",1)[0]
        self.assertIn("last_cell_signatures[sym]=symbol_signature",tick)
        self.assertIn("if last_cell_signatures.get(sym)==symbol_signature:",tick)
        self.assertIn("if cell.page is not None:cell.update()",tick)
        self.assertIn("if freshness.page is not None:freshness.update()",tick)
        self.assertNotIn("request_view_refresh(4)",tick)
        self.assertNotIn("dhan_feed.batch_quotes",tick)

    def test_manual_button_disabled_flag_tracks_login_and_busy_state(self):
        worker=self.source.split("    async def watch_visible_tick():",1)[1].split(
            "    def watchlist():",1)[0]
        self.assertIn("button=watch_refresh_button[0]",worker)
        self.assertIn("button.disabled=should_disable",worker)
        self.assertIn("if button.page is not None:button.update()",worker)
        builder=self.source.split("    def watchlist():",1)[1].split(
            "    symbol=ft.Dropdown(",1)[0]
        self.assertIn("watch_refresh_button[0]=refresh_btn",builder)
        self.assertIn("watch_status_text.value=",builder)

    def test_watchlist_auto_refresh_is_non_destructive(self):
        flush=self.source.split("    async def flush_view_refresh():",1)[1].split(
            "    def request_view_refresh(i):",1)[0]
        self.assertIn("target==4 and current[0]==4",flush)
        self.assertIn("return",flush)
        manual=self.source.split("    async def refresh_all_dhan_quotes():",1)[1].split(
            "    quote_auto_last_attempt=",1)[0]
        self.assertIn("await refresh_watch_batch()",manual)
        self.assertIn("await refresh_dhan_index_quotes(force=True)",manual)
        self.assertNotIn("quotes.clear()",manual)


if __name__ == "__main__":
    unittest.main()
