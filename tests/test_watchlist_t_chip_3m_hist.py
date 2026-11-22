"""Watchlist T chip must show the 3m HIST vote that its own row already shows."""
from pathlib import Path
import unittest

SRC = Path(__file__).resolve().parents[1] / "src" / "main.py"


def chips_body():
    source = SRC.read_text(encoding="utf-8")
    return source.split("    def five_engine_chips(", 1)[1].split("    def super_five_card(", 1)[0]


class WatchlistTChip3mHistTests(unittest.TestCase):
    def test_three_minute_branch_reads_dedicated_3m_cache(self):
        body = chips_body()
        self.assertIn('display_timeframe=="3m"', body)
        self.assertIn("watch_three_minute_cache.get(sym)", body)
        self.assertIn('result3.get("timeframe")=="3m"', body)
        self.assertIn('result3.get("source")=="Dhan"', body)

    def test_reuse_requires_same_generation_and_filter_policy(self):
        body = chips_body()
        self.assertIn("saved3[0][:4]==context3", body)
        for part in ("provider_generation[0]", "tuple(filter_selected)",
                     "tuple(sorted(filter_modes.items()))", 'prefs.get("confidence",75)'):
            self.assertIn(part, body.split("context3=", 1)[1].split("if (isinstance(result3", 1)[0])

    def test_branch_is_read_only_and_never_live(self):
        body = chips_body()
        branch = body.split('display_timeframe=="3m"', 1)[1].split("valid=(type(bull)", 1)[0]
        for forbidden in ("watch_three_minute_signal(", "analyze(", "shared_history(",
                          "dhan_feed.", "request_", "fetch"):
            self.assertNotIn(forbidden, branch)
        self.assertIn("historical=True", branch)
        # Label still carries HIST; a LIVE label is never produced for chips.
        self.assertIn('(" HIST " if historical else " ")', body)
        self.assertNotIn('" LIVE "', body)

    def test_indices_keep_their_own_one_minute_path(self):
        branch = chips_body().split('display_timeframe=="3m"', 1)[1].split("valid=(type(bull)", 1)[0]
        self.assertIn('sym not in ("NIFTY","BANKNIFTY","SENSEX")', chips_body())
        self.assertNotIn("historical_vote_agreement", branch)

    def test_wait_and_market_closed_labels_are_preserved(self):
        body = chips_body()
        self.assertIn('label=short+" WAIT";color=MUTED', body)
        self.assertIn("OFF • market closed", body)

    def test_watchlist_row_and_delta_update_both_use_3m_chip(self):
        source = SRC.read_text(encoding="utf-8")
        self.assertIn('five_engine_chips(sym,display_timeframe="3m")', source)
        self.assertGreaterEqual(source.count('five_engine_chips(sym,display_timeframe="3m")'), 2)


if __name__ == "__main__":
    unittest.main()
