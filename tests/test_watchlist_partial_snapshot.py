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
        self.assertIn('await asyncio.sleep(30)',poll)
        self.assertIn('except asyncio.CancelledError:',poll)
        self.assertIn('raise',poll)

    def test_dhan_history_progress_reports_cached_candles(self):
        text=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        self.assertIn('history_cached=[0]',text)
        self.assertIn('history_cached[0]+=int(bool(data.get("cached")))',text)
        self.assertIn('str(history_cached[0])+" cached"',text)

    def test_dhan_history_prioritizes_scanner_and_super_five_without_fanout(self):
        text=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        self.assertIn('priority=[scan_symbol.value or "NIFTY"]+[row.get("symbol") for row in top5_candidates',text)
        self.assertIn('[sym for sym in priority if sym in symbols]+symbols',text)
        self.assertIn('results.append(await load_one(sym))',text)
        self.assertIn('await asyncio.sleep(1.5)',text)

    def test_historical_votes_keep_colored_proportions_and_warning(self):
        text=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        start=text.index("def strength_widget(")
        end=text.index("def mark_ranking_historical()",start)
        widget=text[start:end]
        self.assertIn("bull_bar_color=GREEN",widget)
        self.assertIn("bear_bar_color=RED",widget)
        self.assertIn("label_color=GREEN",widget)
        self.assertIn('display_prefix="HISTORICAL • " if historical else ""',widget)
        self.assertIn("not win probability",widget)

    def test_server_intraday_reuses_only_recent_exact_window(self):
        server=(Path(__file__).resolve().parents[1]/"backend"/"server.py").read_text(encoding="utf-8")
        start=server.index('@app.post("/dhan/intraday")')
        end=server.index('@app.get("/health")',start)
        block=server[start:end]
        self.assertIn('cached.get("from_date") == body.from_date.isoformat()',block)
        self.assertIn('cached.get("to_date") == body.to_date.isoformat()',block)
        self.assertIn('0 <= age < 180',block)
        self.assertIn('cached.get("bars")',block)
        self.assertIn('freshness": "historical_unverified"',block)
        self.assertIn('"last_candle_timestamp": int(cached["bars"][-1][0])',block)
        self.assertIn('"last_candle_timestamp": int(bars[-1][0]) if bars else None',block)

    def test_closed_session_dhan_429_does_not_schedule_auto_retry(self):
        text=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        start=text.index("# On a closed session, one transient all-symbol failure")
        end=text.index("async def supervised_market_refresh():",start)
        block=text[start:end]
        self.assertIn('and not any("rate limited" in reason.lower() or "cooldown" in reason.lower()',block)
        self.assertIn('or "http 429" in reason.lower()',block)
        self.assertIn('closed_session_retry_generation!=generation',block)

    def test_history_refresh_rejects_invalid_cached_dhan_price(self):
        text=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        start=text.index("async def load_one(sym):")
        end=text.index("# Fail fast on a broken Dhan history endpoint.",start)
        history=text[start:end]
        self.assertIn('isinstance(latest.get("price"),(int,float))',history)
        self.assertIn('not isinstance(latest.get("price"),bool)',history)
        self.assertIn('math.isfinite(latest["price"])',history)
        self.assertIn('data=dict(data,price=latest["price"]',history)

    def test_invalid_dhan_batch_prices_cannot_overwrite_last_good_quotes(self):
        text=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        guard='isinstance(snapshot.get("price"),(int,float)) and not isinstance(snapshot.get("price"),bool) and math.isfinite(snapshot["price"])'
        self.assertGreaterEqual(text.count(guard),2)
        self.assertIn('if ticker in all_watch_symbols() and snapshot.get("source")=="Dhan" and '+guard+' and snapshot["price"]>0:',text)
        self.assertIn('if ticker in all_watch_symbols() and snapshot.get("source") == "Dhan" and '+guard+':',text)

    def test_dhan_history_cooldown_does_not_rank_unattempted_symbols(self):
        text=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        start=text.index("                # Fail fast on a broken Dhan history endpoint.")
        end=text.index("                # Fresh candle-only Top 5;",start)
        history=text[start:end]
        self.assertIn("if not first_ok and symbols[0] in failed_symbols:",history)
        self.assertIn("Dhan historical feed unavailable",history)
        self.assertIn("Dhan historical scan paused after HTTP 429",history)
        self.assertIn("symbols not attempted",history)
        self.assertIn("last_scanned_generation=None",history)
        self.assertIn("last ranking retained",history)
        self.assertIn("if not cache_ready:",history)
        self.assertIn("await asyncio.sleep(1.5)",history)

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
