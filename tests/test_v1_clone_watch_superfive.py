"""Targeted regression for the owner's two V1-clone findings.

These checks forbid fictional live signals and prevent accidentally changing
the rest of the original V1 shell while repairing Watchlist and Super Five.
"""
import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "main.py"


class WatchlistSuperFiveCloneRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SRC.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)
        cls.functions = {n.name: n for n in ast.walk(cls.tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

    def segment(self, name):
        node = self.functions[name]
        return "\n".join(self.source.splitlines()[node.lineno - 1:node.end_lineno])

    def test_watchlist_entry_warms_only_existing_bounded_three_minute_lane(self):
        render = self.segment("render_page")
        warm = self.segment("warm_selected_watch_three_minute_early")
        self.assertIn('changed and i==4 and refresh_hours()', render)
        self.assertIn('page.run_task(warm_selected_watch_three_minute_early,provider_generation[0])', render)
        self.assertIn('dhan_feed.cooldown_remaining("/dhan/intraday")>0', warm)
        self.assertIn('len(watch_three_minute_upstream_times)>=3', warm)
        self.assertIn('get_market_data,sym,"1m","2d"', warm)
        self.assertIn('live_verified=False', warm)

    def test_watchlist_green_red_uses_matching_three_minute_votes(self):
        signal = self.segment("compact_watch_signal")
        self.assertIn('row.get("timeframe")=="3m"', signal)
        self.assertIn('return vote_display(counts,False,timeframe="3m")', signal)
        self.assertIn('matching 3m candles / valid votes unavailable', signal)

    def test_super_five_historical_bias_not_promoted_as_live(self):
        ranking = self.segment("publish_partial_ranking")
        card = self.segment("super_five_card")
        self.assertEqual(ranking.count('row.get("bias") if row.get("bias") in ("BULLISH","BEARISH")'), 2)
        self.assertEqual(ranking.count('score=0,historical=True,live_verified=False'), 2)
        self.assertIn('"HISTORICAL "+row["bias"]+" • NOT LIVE"', card)
        self.assertIn('else "NO LIVE SIGNAL" if historical', card)
        self.assertIn('rank_candidates(', ranking)

    def test_legacy_shell_login_and_sources_untouched(self):
        s = self.source
        for token in ('api_url=ft.TextField(', 'server_access=ft.TextField(', 'server_trust=ft.Checkbox(', 'ServerAngelFeed', 'get_yahoo(', 'def watchlist():', 'def super_five_card():'):
            self.assertIn(token, s)


if __name__ == "__main__":
    unittest.main()
