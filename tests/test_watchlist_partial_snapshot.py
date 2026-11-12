"""Guard last-valid Dhan prices without misreporting partial refresh coverage."""
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
        self.assertIn('received=sum(1 for ticker in all_watch_symbols()',watch)
        self.assertIn('snapshot.get("source")=="Dhan"',watch)
        self.assertIn('math.isfinite(snapshot["price"])',watch)
        self.assertIn("received<total_symbols",watch)
        self.assertIn("valid prices returned",watch)
        self.assertIn("Dhan LTP loaded: {received}/{total_symbols} valid prices",watch)
        self.assertNotIn("Dhan LTP loaded: {count}",watch)
        self.assertIn("timestamps unverified",watch)
        self.assertIn("Dhan quote refresh interrupted in background",watch)
        self.assertIn("if not app_active[0]:",watch)
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

    def test_watchlist_batch_rejects_duplicate_and_disconnected_requests(self):
        text=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        start=text.index("    async def refresh_watch_batch():")
        end=text.index("    async def dhan_quote_poll():",start)
        watch=text[start:end]
        self.assertIn('if watch_batch_busy[0] or prefs.get("source")!="Dhan":',watch)
        self.assertIn('if not dhan_feed.connected:',watch)
        self.assertIn('watch_batch_busy[0]=True',watch)
        self.assertIn('finally:',watch)
        self.assertIn('watch_batch_busy[0]=False',watch)
        self.assertIn('if generation!=provider_generation[0] or prefs.get("source")!="Dhan":',watch)

    def test_dhan_snapshot_polling_is_foreground_only_and_rate_limited(self):
        text=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        start=text.index("    async def dhan_quote_poll():")
        end=text.index("    def watchlist():",start)
        poll=text[start:end]
        self.assertIn('app_active[0] and prefs.get("source")=="Dhan"',poll)
        self.assertIn('dhan_feed.connected',poll)
        self.assertIn('dhan_feed.cooldown_remaining("/v2/snapshot")==0',poll)
        self.assertIn('await refresh_watch_batch()',poll)
        self.assertIn('await asyncio.sleep(45)',poll)
        self.assertIn('except asyncio.CancelledError:',poll)
        self.assertIn('raise',poll)

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
