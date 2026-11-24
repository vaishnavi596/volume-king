"""B1 read-only five-engine integration: one Dhan option request and no false votes."""
import unittest
from pathlib import Path
from test_audit import start

ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/"src"/"main.py").read_text(encoding="utf-8")


class FiveEngineDhanReadOnlyTests(unittest.TestCase):
    def test_shared_option_poll_only_for_selected_dhan_pages(self):
        block=SOURCE.split("    async def option_poll():",1)[1].split("    def selected_option_rows():",1)[0]
        self.assertIn("current[0] in (0,1,3)",block)
        self.assertIn('prefs.get("source")=="Dhan"',block)
        self.assertIn('chain_symbol.value in DHAN_VERIFIED_SYMBOLS',block)
        self.assertIn('dhan_feed.connected',block)
        self.assertIn('dhan_option_last_attempt[0]>=60',block)
        self.assertIn("await refresh_selected_options()",block)
        self.assertNotIn('get_market_data(',block)
        self.assertNotIn('quotes[sym]=hist',block)

    def test_options_are_context_only_even_with_pcr(self):
        _,v=start({"scanner_live":False,"source":"Dhan"})
        v["dhan_option_metrics"].update(source="dhan",symbol="NIFTY",
            expiry=v["expiry"].value,pcr=0.83,max_pain=25000,
            freshness="unverified",signal_eligible=False)
        chips=v["five_engine_chips"]("NIFTY")
        values=[card.content.value for group in chips.controls for card in group.controls]
        # Disconnected test page must never pretend it received a verified vote.
        self.assertEqual(len(values),6)
        self.assertEqual(values[5],"6  —")  # Blank, inert reserved display only.
        self.assertTrue(all(("WAIT" in label or "HIST" in label or label.endswith(" OFF")) for label in values[:5]))
        self.assertNotIn("O B", " ".join(values))

    def test_independent_candle_history_never_claims_verified_signal(self):
        from five_engine import historical_candle_balance, compose_snapshot
        bars=[(1700000000+i*300,100,102,98,101 if i%4 else 99,50)
              for i in range(8)]
        result=historical_candle_balance(bars)
        self.assertEqual(result["bullish"],75)
        self.assertEqual(result["bearish"],25)
        self.assertTrue(result["historical"])
        self.assertFalse(result["verified"])
        self.assertEqual(compose_snapshot()["combined"]["state"],"WAIT")
        self.assertIsNone(historical_candle_balance(bars[:4]))
        self.assertIsNone(historical_candle_balance(bars[:-1]+[bars[-2]]))

    def test_historical_candle_chip_never_fetches_broker_data(self):
        chip=SOURCE.split("    def five_engine_chips(sym, display_timeframe=None):",1)[1].split("    def super_five_card():",1)[0]
        self.assertIn("C HIST B",chip)
        self.assertIn("NOT live",chip)
        self.assertNotIn("dhan_feed.option_chain",chip)
        self.assertNotIn("asyncio.to_thread",chip)
        self.assertNotIn("get_market_data(",chip)

    def test_no_extra_poll_on_dashboard_render(self):
        view=SOURCE.split("    def dashboard():",1)[1].split("    search=ft.TextField(",1)[0]
        self.assertNotIn("dhan_feed.option_chain_metrics",view)
        self.assertNotIn("dhan_feed.option_expiries",view)

    def test_futures_not_promoted_without_broker_contract(self):
        from five_engine import futures_from_component, compose_snapshot
        e=futures_from_component({"source":"Dhan","verified":False,
            "contract":"NIFTY FUT","timestamp":1730000000,
            "ltp":25000,"open_interest":100,"volume":10})
        self.assertFalse(e.eligible)
        combined=compose_snapshot(futures=e)["combined"]
        self.assertEqual(combined["state"],"WAIT")
        self.assertEqual(combined["coverage"],0)

    def test_option_metrics_require_read_only_unverified_contract(self):
        from five_engine import option_chain_display_context
        self.assertFalse(option_chain_display_context({
            "source":"Dhan","signal_eligible":True,"freshness":"exchange_verified"
        })["available"])


if __name__=="__main__":
    unittest.main()
