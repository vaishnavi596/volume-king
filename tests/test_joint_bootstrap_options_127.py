"""127-C/D: closed-market Super Five and Dhan-only options session wiring."""
from pathlib import Path
import unittest

SRC=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
def segment(a,b):
    return SRC.split(a,1)[1].split(b,1)[0]

class JointSessionRepairTests(unittest.TestCase):
    def test_login_starts_options_even_after_market_close(self):
        body=segment("    async def connect_angel():","    def provider_changed(")
        self.assertIn('page.run_task(refresh_selected_options)',body)
        start=body.index("page.run_task(refresh_selected_options)")
        self.assertIn('dhan_feed.connected',body[start-230:start])
        self.assertNotIn('regular_hours()',body[start-230:start])
        self.assertIn("page.run_task(refresh_dhan_index_quotes,True)",body)

    def test_closed_market_cached_top_five_requires_no_provider_call(self):
        body=segment("    async def super_five_minute_refresh():","    def five_engine_summary(symbol):")
        self.assertNotIn("not regular_hours()",body)
        self.assertIn('bars=snapshot.get("bars") or []',body)
        self.assertIn("publish_partial_ranking(results)",body)
        # Checking connection state is allowed; no provider endpoint is called.
        self.assertIn("dhan_feed.connected",body)
        self.assertNotIn("dhan_feed.batch_quotes(",body)
        self.assertNotIn("dhan_feed.intraday(",body)
        self.assertNotIn("dhan_feed.option_chain_metrics(",body)
        change=segment("    def provider_changed(e):","    broker_previous=broker.on_change")
        self.assertIn("publish_partial_ranking({})",change)
        chips=segment("    def five_engine_chips(sym):","    def super_five_card():")
        self.assertIn("top5_candidates",chips)
        self.assertIn('row.get("historical") is True',chips)
        self.assertIn('row.get("source")=="Dhan"',chips)
        self.assertIn('historical=True',chips)
        self.assertIn("signal_percentages(raw)",chips)

    def test_super_five_news_is_bounded_context_not_an_engine_vote(self):
        news=segment("    news_bootstrap_generation=[None]","    async def super_five_minute_refresh():")
        self.assertIn("news_bootstrap_generation[0]=generation",news)
        self.assertIn("[:5]",news)
        self.assertIn("await asyncio.to_thread(fetch_news,sym)",news)
        self.assertIn("await asyncio.sleep(0.5)",news)
        self.assertNotIn("dhan_feed.option_chain_metrics",news)
        self.assertNotIn("dhan_feed.batch_quotes",news)
        login=segment("    async def connect_angel():","    def provider_changed(")
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
        context=segment("    def five_engine_summary(symbol):","    def super_five_card():")
        self.assertIn("gen==provider_generation[0]",context)
        self.assertIn("underlying==sym",context)
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
