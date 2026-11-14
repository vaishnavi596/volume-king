"""Batch 4 compact watchlist: short statuses, retained vote provenance and row actions."""
from pathlib import Path
import unittest

SOURCE=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")

class CompactWatchlistTest(unittest.TestCase):
    def test_compact_vote_bar_and_provenance(self):
        body=SOURCE.split("    def compact_watch_signal(",1)[1].split("    def fill_watch(",1)[0]
        self.assertIn('label=("LIVE" if fresh else "HIST")',body)
        self.assertIn('height=4',body)
        self.assertIn('if not counts:',body)
        self.assertIn('if total<=0:',body)
        self.assertIn('signal_percentages(row)',body)

    def test_row_preserves_price_source_and_detail_navigation(self):
        body=SOURCE.split("    def fill_watch(",1)[1].split("    search.on_change=fill_watch",1)[0]
        self.assertIn("compact_watch_signal(signal_row,signal_available,signal_fresh)",body)
        self.assertIn("quote_price(sym) if quote_source==expected_quote_source",body)
        self.assertIn("open_stock(v)",body)
        self.assertIn("remove_stock(v)",body)
        self.assertNotIn('note(quote_label),strength_widget(signal_row,sym)',body)

if __name__=="__main__":unittest.main()
