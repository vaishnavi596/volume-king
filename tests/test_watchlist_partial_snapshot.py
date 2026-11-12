"""Guard against showing stale equity prices after a partial Dhan snapshot."""
import unittest
from pathlib import Path


class WatchlistPartialSnapshotTests(unittest.TestCase):
    def test_missing_quotes_are_cleared_before_publishing_batch(self):
        text=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        start=text.index("    async def refresh_watch_batch():")
        end=text.index("        finally:",start)
        body=text[start:end]
        self.assertIn('if ticker not in batch and (quotes.get(ticker) or {}).get("source")=="Dhan":',body)
        self.assertIn('quotes.pop(ticker,None)',body)
        self.assertLess(body.index('quotes.pop(ticker,None)'),body.index('for ticker,snapshot in batch.items():'))
        self.assertIn('missing prices cleared',body)

    def test_connect_batch_clears_missing_and_failed_quotes(self):
        text=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        start=text.index('# Verify watchlist batch independently of the login check.')
        end=text.index('                    if market_status.startswith("Dhan connected; watchlist batch failed"):',start)
        body=text[start:end]
        self.assertIn('if ticker not in batch and (quotes.get(ticker) or {}).get("source")=="Dhan":',body)
        error=body[body.index("log_error('dhan_batch_after_connect',exc)"):]
        self.assertIn('dhan_batch_cache.update(generation=None,updated=0.0,quotes={})',error)
        self.assertIn('quotes.pop(ticker,None)',error)

    def test_failed_watchlist_snapshot_invalidates_cached_quotes(self):
        text=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        start=text.index("    async def refresh_watch_batch():")
        end=text.index("    async def dhan_quote_poll():",start)
        body=text[start:end]
        error=body[body.index('log_error("watchlist_dhan_batch",exc)'):]
        self.assertIn('dhan_batch_cache.update(generation=None,updated=0.0,quotes={})',error)
        self.assertIn('quotes.pop(ticker,None)',error)

    def test_background_scanner_failure_invalidates_old_quotes(self):
        text=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        start=text.index('scan_progress["state"]="Checking Dhan batch before historical scan"')
        end=text.index('                # Connection is now ready:',start)
        body=text[start:end]
        error=body[body.index('log_error("dhan_batch",exc)'):]
        self.assertIn('dhan_batch_cache.update(generation=None,updated=0.0,quotes={})',error)
        self.assertIn('if generation==provider_generation[0] and prefs.get("source")=="Dhan":',error)
        self.assertIn('quotes.pop(ticker,None)',error)

    def test_background_scanner_also_clears_missing_quotes(self):
        text=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        start=text.index('scan_progress["state"]="Checking Dhan batch before historical scan"')
        end=text.index('                # Connection is now ready:',start)
        body=text[start:end]
        self.assertIn('if ticker not in batch and (quotes.get(ticker) or {}).get("source")=="Dhan":',body)
        self.assertIn('quotes.pop(ticker,None)',body)
        self.assertLess(body.index('quotes.pop(ticker,None)'),body.index('for ticker, snapshot in batch.items():'))


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
