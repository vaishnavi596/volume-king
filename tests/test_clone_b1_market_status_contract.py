"""Batch 1 UI contract: market status must never claim LIVE from timestamp-unverified quotes."""
import ast
import unittest
from pathlib import Path


class CloneB1StatusContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path(__file__).resolve().parents[1].joinpath("src/main.py").read_text()
        ast.parse(cls.source)

    def test_off_market_and_stale_unverified_label(self):
        self.assertIn('Data mode: LIVE (verified) / HISTORICAL (last completed)', self.source)
        self.assertIn('Missing evidence stays WAIT; cached quote never becomes LIVE', self.source)
        self.assertNotIn('market_display_choice=ft.Dropdown(', self.source)
        self.assertIn('LIVE quote/session unverified • 0/5 verified', self.source)

    def test_mounted_watchlist_compact_status(self):
        self.assertIn('label=("OFF" if not regular_hours() else "STALE")', self.source)
        self.assertIn('" • ERROR" if watch_batch_status[0].startswith', self.source)

    def test_obsolete_callback_instruction_replaced(self):
        self.assertNotIn('Clone browser Dhan consent requires separate approved Clone callback', self.source)
        self.assertIn('Existing Oracle callback: /dhan/callback', self.source)

    def test_price_status_uses_shared_session_caption(self):
        self.assertIn('f"Dhan connected • {received}/{total_symbols} LTP • "', self.source)
        # The old Angel/V1 login callback was retired. The active Dhan
        # batch status still uses the shared closed/stale session caption.
        self.assertIn('+ session_caption())', self.source)

    def test_chart_timeframe_selector_matches_derivation(self):
        self.assertIn('["1m","2m","3m","5m","10m","15m","30m","1h"]', self.source)
        self.assertIn('source_interval=("1m" if interval in ("2m","3m")', self.source)

    def test_watchlist_updates_in_place_and_no_fake_live(self):
        self.assertIn('async def watch_visible_tick()', self.source)
        self.assertIn('if current[0]!=4 or not app_active[0] or lifecycle_background[0]:', self.source)
        self.assertIn('"live_verified":False', self.source)


if __name__ == "__main__":
    unittest.main()
