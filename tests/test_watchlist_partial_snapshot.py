"""Guard against showing stale equity prices after a partial Dhan snapshot."""
import unittest
from pathlib import Path


class WatchlistPartialSnapshotTests(unittest.TestCase):
    def test_all_dhan_batch_paths_keep_last_valid_quote_and_report_failure(self):
        text=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        start=text.index("    async def refresh_watch_batch():")
        end=text.index("    async def dhan_quote_poll():",start)
        watch=text[start:end]
        self.assertNotIn("quotes.pop(ticker,None)",watch)
        self.assertIn("previous quotes retained",watch)
        self.assertIn("Dhan batch failed:",watch)
        self.assertIn("dhan_batch_issue[0]=safe_error(exc)",watch)
        start=text.index("# Verify watchlist batch independently of the login check.")
        end=text.index('                    if market_status.startswith("Dhan connected; watchlist batch failed"):',start)
        login=text[start:end]
        self.assertNotIn("quotes.pop(ticker,None)",login)
        self.assertIn("Partial Dhan batch:",login)
        start=text.index('scan_progress["state"]="Checking Dhan batch before historical scan"')
        end=text.index('                # Connection is now ready:',start)
        scanner=text[start:end]
        self.assertNotIn("quotes.pop(ticker,None)",scanner)
        self.assertIn("Dhan batch LTP unavailable:",scanner)
        self.assertIn("dhan_batch_cache.update(generation=None,updated=0.0,quotes={})",scanner)

    def test_dhan_history_has_one_pacing_delay_not_two(self):
        text=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        start=text.index("                async def load_one(sym):")
        end=text.index("                # Fail fast on a broken Dhan history endpoint.",start)
        self.assertNotIn("await asyncio.sleep(0.8)",text[start:end])
        start=text.index("                    for sym in symbols[1:]:",end)
        end=text.index("                else:\n                    results=await asyncio.gather",start)
        self.assertIn("await asyncio.sleep(1.5)",text[start:end])


if __name__=="__main__":
    unittest.main()
