"""127-C/D: closed-market Super Five and Dhan-only options session wiring."""
from pathlib import Path
import unittest

SRC=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
def segment(a,b):
    return SRC.split(a,1)[1].split(b,1)[0]

class JointSessionRepairTests(unittest.TestCase):
    def test_login_starts_options_even_after_market_close(self):
        body=segment("    async def check_clone_v2_connection():","    def check_clone_v2_gateway(e):")
        self.assertIn('page.run_task(refresh_selected_options)',body)
        start=body.index("page.run_task(refresh_selected_options)")
        self.assertIn('dhan_feed.connected',body[start-230:start])
        self.assertNotIn('regular_hours()',body[start-230:start])
        # The initial combined Dhan batch already owns index readiness.
        self.assertNotIn("page.run_task(refresh_dhan_index_quotes,True)",body)
        self.assertIn("index_last_attempt[0]=time.monotonic()",body)

    def test_closed_market_cached_top_five_requires_no_provider_call(self):
        body=segment("    async def super_five_minute_refresh():","    def five_engine_summary(symbol, display_timeframe=None):")
        self.assertNotIn("not regular_hours()",body)
        self.assertIn('bars=data.get("bars") or []',body)
        self.assertIn("await local_analysis_pool.run(display_analysis,sym,snapshot,frozen=frozen)",body)
        self.assertIn("revision(capture())!=fingerprint[-1]",body)
        self.assertIn("publish_partial_ranking(results)",body)
        # Cached completed Dhan candles must remain available as HIST even after disconnect.
        # Local recomputation must not invoke any provider endpoint.
        self.assertIn("shared_history(sym)",body)
        self.assertIn("valid_candle_history(bars)",body)
        self.assertNotIn('and not dhan_feed.connected',body)
        self.assertNotIn("dhan_feed.batch_quotes(",body)
        self.assertNotIn("dhan_feed.intraday(",body)
        self.assertNotIn("dhan_feed.option_chain_metrics(",body)
        change=segment("    def provider_changed(e):","    broker_previous=broker.on_change")
        self.assertIn("publish_partial_ranking({})",change)
        chips=segment("    def five_engine_chips(sym, display_timeframe=None):","    def super_five_card():")
        self.assertIn("top5_candidates",chips)
        self.assertIn('row.get("historical") is True',chips)
        self.assertIn('row.get("source")=="Dhan"',chips)
        self.assertIn('historical=True',chips)
        self.assertIn("signal_percentages(raw)",chips)

    def test_super_five_news_is_bounded_context_not_an_engine_vote(self):
        news=segment("    news_bootstrap_generation=[None]","    async def super_five_minute_refresh():")
        self.assertIn("news_bootstrap_generation[0]=generation",news)
        self.assertIn("[:5]",news)
        # Without saved Top Five, prime no more than five equity RSS contexts.
        self.assertIn("selected_news_symbols=all_watch_symbols()",news)
        self.assertIn("for sym in selected_news_symbols:",news)
        self.assertIn("if len(candidates)>=5:",news)
        self.assertIn("if sym not in candidates:",news)
        self.assertIn("candidates.append(sym)",news)
        self.assertIn("await asyncio.to_thread(fetch_news,sym)",news)
        self.assertIn("await asyncio.sleep(0.5)",news)
        self.assertNotIn("dhan_feed.option_chain_metrics",news)
        self.assertNotIn("dhan_feed.batch_quotes",news)
        login=segment("    async def check_clone_v2_connection():","    def check_clone_v2_gateway(e):")
        self.assertIn("page.run_task(refresh_superfive_news)",login)
        rss=segment("    def fetch_news(symbol,global_news=False):","    def headline_signal(items):")
        self.assertIn("response.read(262_145)",rss)
        self.assertIn("len(raw)>262_144",rss)
        self.assertNotIn("2_000_001",rss)
        context=segment("    def combine_analysis(symbol,interval,candle,local_news,global_news):","    async def load_combined(symbol,interval,candle):")
        self.assertIn("news_bias=None",context)
        self.assertIn("no confirmed combined setup",context)

    def test_multi_underlying_option_context_isolated_to_session(self):
        body=segment("    async def refresh_selected_options():","    async def option_poll():")
        self.assertIn("dhan_option_context_cache[(generation,sym,chosen)]",body)
        self.assertIn("len(dhan_option_context_cache)>16",body)
        self.assertIn("generation!=provider_generation[0]",body)
        self.assertIn("await asyncio.sleep(3.25)",body)
        context=segment("    def five_engine_summary(symbol, display_timeframe=None):","    def super_five_card():")
        self.assertIn("gen==provider_generation[0]",context)
        self.assertIn("matching_option_context_for_symbol(sym)",context)
        reader=segment("    def matching_option_context_for_symbol(sym):","    def enrich_context_filter_rows(sym,rows):")
        self.assertIn("gen==generation and underlying==sym",reader)
        self.assertIn("generation=provider_generation[0]",reader)
        self.assertIn("listed==expiry.value",reader)
        self.assertIn('data.get("signal_eligible") is False',reader)
        self.assertIn('market_store.get("option_context_last_good","Dhan",sym,listed)',reader)
        self.assertIn("symbol!=chain_symbol.value",context)
        self.assertIn("data.get(\"signal_eligible\") is False",context)

    def test_option_retry_guard_is_per_selection_and_provider_cooldown(self):
        body=segment("    async def refresh_selected_options():","    def selected_option_rows():")
        self.assertIn('option_key=(provider_generation[0],chain_symbol.value',body)
        self.assertIn('expiry.value if option_expiry_choice.value=="Manual" else ""',body)
        self.assertIn('option_retry_until.get(option_key,0.0)',body)
        self.assertIn('delay=(300 if "422" in detail',body)
        self.assertIn('if "429" in detail or "cooldown" in detail.lower()',body)
        self.assertIn('option_retry_until[option_key]=time.monotonic()+delay',body)
        self.assertIn("and sym==chain_symbol.value",body)
        self.assertIn("and choice==option_expiry_choice.value",body)
        self.assertIn('option_retry_until.pop(option_key,None)',body)
        self.assertIn('len(option_retry_until)>32',body)
        self.assertIn('and dhan_feed.cooldown_remaining("/dhan/option-chain")==0',body)
        self.assertIn('and dhan_feed.cooldown_remaining("/dhan/option-expiries")==0',body)
        self.assertIn('last saved context unverified',body)

    def test_selected_equity_error_exposed_on_login_and_poll(self):
        main=segment('    async def refresh_watch_batch():','    index_refresh_busy=[False]')
        self.assertIn('selected_batch_issue[0]=safe_error(exc)[:120]',main)
        self.assertIn('selected equities unavailable: ',main)
        self.assertIn('login_bootstrap.finish(generation,"equities"',main)
        login=segment('    async def check_clone_v2_connection():','    def check_clone_v2_gateway(e):')
        self.assertIn('dhan_batch_issue[0]=(',login)
        self.assertIn('f"Partial Clone B3 Dhan batch: {found}/{total} validated"',login)
        self.assertIn('watch_batch_status[0]=(',login)
        self.assertIn('login_bootstrap.finish(provider_generation[0],"equities",found,total)',login)

    def test_no_live_orders_and_paper_center_retained(self):
        self.assertIn("content.append(paper_trading_center())",SRC)
        self.assertIn('note("Paper Bot: "+paper_bot_state[0]',SRC)
        self.assertIn('paper_bot_state[0]="Running"',SRC)
        self.assertIn('if not manual_contract_confirmed.value:',SRC)
        self.assertIn('section("REAL TRADING • DISABLED"',SRC)
        self.assertIn("Live broker orders OFF",SRC)
        self.assertNotIn("dhan_feed.place_order",SRC)

if __name__=="__main__":
    unittest.main()
