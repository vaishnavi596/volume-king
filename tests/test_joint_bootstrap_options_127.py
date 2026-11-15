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
        self.assertNotIn("dhan_feed.",body)
        change=segment("    def provider_changed(e):","    broker_previous=broker.on_change")
        self.assertIn("publish_partial_ranking({})",change)

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

    def test_no_live_orders_and_paper_center_retained(self):
        self.assertIn("content.append(paper_trading_center())",SRC)
        self.assertIn('section("REAL TRADING • DISABLED"',SRC)
        self.assertIn("Live broker orders OFF",SRC)
        self.assertNotIn("dhan_feed.place_order",SRC)

if __name__=="__main__":
    unittest.main()
