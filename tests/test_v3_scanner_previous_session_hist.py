"""Previous-session scanner data can be HIST without being verified LIVE.

Source contract + pure offline data checks. No provider calls or broker orders.
"""
import pathlib
import sys
import unittest
from datetime import datetime, timedelta, timezone

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from analysis_quality import quality_check
from historical_session_window import historical_regular_session_bars
from scanner_engine import analyze

IST=timezone(timedelta(hours=5,minutes=30))
TF=60

def past_session():
    start=int(datetime(2026,11,20,9,15,tzinfo=IST).timestamp())
    return [[start+i*TF,25000.0+i,25001.0+i,24999.0+i,25000.5+i,100.0]
            for i in range(50)]

class ScannerPreviousSessionGate(unittest.TestCase):
    def test_exact_scanner_historical_gate_anchors_last_completed_bar(self):
        main=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
        source=main[main.index("historical_bars=historical_regular_session_bars(bars,interval)"):]
        source=source[:source.index("if history_valid:")]
        self.assertIn('now=historical_bars[-1][0]+timeframe_spec(interval)["seconds"]',source)
        self.assertIn('historical.get("timestamp")==historical_bars[-1][0]',source)
        self.assertIn('historical.get("count",0)>=30',source)

    def test_previous_session_is_historical_quality_not_live_fresh(self):
        bars=past_session()
        self.assertFalse(quality_check(bars,TF)["usable"])
        hist=quality_check(bars,TF,now=bars[-1][0]+TF)
        self.assertTrue(hist["usable"],hist["reasons"])
        result=analyze(hist["bars"],["EMA 9/21","RSI 14"],"1m")
        self.assertEqual(result["count"],len(bars))
        self.assertTrue(result["votes"])

    def test_after_close_suffix_is_excluded_without_fabricating_bars(self):
        bars=past_session()
        after=int(datetime(2026,11,20,19,57,tzinfo=IST).timestamp())
        extended=bars+[[after,25100,25100,25100,25100,0]]
        trimmed=historical_regular_session_bars(extended,"1m")
        self.assertEqual(trimmed,bars)
        self.assertTrue(quality_check(trimmed,TF,now=trimmed[-1][0]+TF)["usable"])
        self.assertEqual(len(extended),51)

    def test_in_session_missing_candle_still_blocks_votes(self):
        bars=past_session()
        damaged=bars[:15]+bars[16:]
        hist=quality_check(damaged,TF,now=damaged[-1][0]+TF)
        self.assertTrue(hist["usable"])  # finite OHLC alone is not cadence proof
        result=analyze(hist["bars"],["EMA 9/21"],"1m")
        self.assertEqual(result["bias"],"WAIT")
        self.assertEqual(result["votes"],[])
        self.assertIn("Irregular candle spacing",result["reason"])

if __name__=="__main__":
    unittest.main()
