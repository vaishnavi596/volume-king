"""Offline 18-filter wiring provenance and historical display regression."""
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from scanner_engine import ALL_FILTERS
from filter_wiring_audit import filter_wiring_matrix


class V3FilterWiringTests(unittest.TestCase):
    def test_registry_exactly_eighteen_unique(self):
        self.assertEqual(len(ALL_FILTERS),18)
        self.assertEqual(len(set(ALL_FILTERS)),18)

    def test_same_18_filters_every_symbol_data_vs_wiring(self):
        rows=[{"name":name,"vote":1,"detail":"historical calculation"}
              for name in ALL_FILTERS if name not in
              {"OI Support","OI Resistance","OI Profile","Dhan Max Pain","News Headlines"}]
        for symbol in ("NIFTY","BANKNIFTY","SENSEX","RELIANCE"):
            self.assertTrue(symbol)
            result=filter_wiring_matrix(ALL_FILTERS,rows,source="Dhan",
                timeframe="1m",candle_ready=True,options_context=True,news_context=True)
            self.assertEqual(len(result),18)
            self.assertEqual(sum(x["state"]=="CALCULATED" for x in result),13)
            self.assertEqual(sum(x["state"]=="ADAPTER_NOT_DIRECTIONAL" for x in result),5)
            self.assertTrue(all(x["vote"] is None for x in result
                                if x["state"]=="ADAPTER_NOT_DIRECTIONAL"))

    def test_missing_option_or_news_does_not_hide_calculated_candles(self):
        rows=[{"name":"RSI 14","vote":0}]
        result=filter_wiring_matrix(["RSI 14","OI Support","News Headlines"],rows,
            candle_ready=True,options_context=False,news_context=False)
        self.assertEqual([x["state"] for x in result],
            ["CALCULATED","OPTION_DATA_MISSING","NEWS_DATA_MISSING"])
        self.assertEqual(result[0]["vote"],0)

    def test_invalid_candles_cannot_pretend_to_vote(self):
        result=filter_wiring_matrix(["Supertrend"],[{"name":"Supertrend","vote":1}],
                                   candle_ready=False)
        self.assertEqual(result[0]["state"],"CANDLE_DATA_MISSING_OR_INVALID")
        self.assertIsNone(result[0]["vote"])

    def test_historical_3m_display_uses_exact_watch_cache_no_fanout(self):
        src=(ROOT/"src/main.py").read_text(encoding="utf-8")
        block=src.split("    def five_engine_chips(",1)[1].split("    def super_five_card(",1)[0]
        self.assertIn('display_timeframe=="3m"',block)
        self.assertIn("three=watch_three_minute_signal(sym)",block)
        self.assertIn('display_timeframe=="1m"',block)
        self.assertIn('shared_history(sym,"1m")',block)
        self.assertIn("filter_wiring_matrix(",src)
        self.assertIn('"filter_wiring_matrix":wiring_matrix',src)


if __name__=="__main__":
    unittest.main()
