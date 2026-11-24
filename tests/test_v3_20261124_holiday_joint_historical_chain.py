"""24-Nov NSE/BSE holiday: combined 1m/3m/5m HIST and five-engine vote gate.

Real local engine functions, actual 23-Nov completed OHLCV fixture, no
provider calls, no fake LIVE votes, no token or Oracle changes.
"""
import pathlib
import sys
import unittest
from datetime import datetime, timedelta, timezone

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from v3_equity_session_calendar import regular_equity_hours, equity_refresh_window, equity_session_closed_detail, IST
from v3_historical_vote_replay import historical_vote_replay
from historical_session_window import historical_regular_session_bars
from scanner_engine import analyze
from filter_wiring_audit import CANDLE_FILTERS

HOLIDAY=datetime(2026,11,24,11,30,tzinfo=IST)

def completed_bars(frame):
    seconds={"1m":60,"3m":180,"5m":300}[frame]
    start=int(datetime(2026,11,23,9,15,tzinfo=IST).timestamp())
    count={"1m":375,"3m":125,"5m":75}[frame]
    return [[start+i*seconds,25000.0+i*.3,25003.0+i*.3,
             24998.0+i*.3,25001.0+i*.3,100+i]
            for i in range(count)]

class HolidayHistoricalChainTests(unittest.TestCase):
    def test_actual_2026_11_24_market_is_closed_and_refresh_suspended(self):
        self.assertFalse(regular_equity_hours(HOLIDAY))
        self.assertFalse(equity_refresh_window(HOLIDAY))
        self.assertIn("trading holiday",equity_session_closed_detail(HOLIDAY))

    def test_all_three_timeframes_preserve_prior_session_t_c_and_abstain_nfo(self):
        for frame in ("1m","3m","5m"):
            with self.subTest(timeframe=frame):
                bars=completed_bars(frame)
                original=[row[:] for row in bars]
                selected=[{"name":"EMA 9/21"},{"name":"RSI 14"},{"name":"MACD"},
                          {"name":"News Headlines"},{"name":"OI Support"}]
                result=historical_vote_replay(
                    symbol="NIFTY",timeframe=frame,generation=7,source="Dhan",
                    bars=bars,filter_rows=selected,
                    history_timestamp=HOLIDAY.timestamp())
                self.assertEqual(bars,original)
                self.assertEqual(result["mode"],"HIST_REPLAY_READ_ONLY")
                self.assertTrue(result["historical"])
                self.assertFalse(result["verified_live"])
                self.assertEqual(result["orders_sent"],0)
                self.assertEqual(result["provider_requests"],0)
                self.assertTrue(result["technical_recomputed_from_completed_bars"])
                self.assertEqual(len(result["boxes"]),5)
                self.assertEqual([r["state"] for r in result["boxes"][:2]],
                                 ["HIST_VOTE","HIST_VOTE"])
                self.assertEqual([r["state"] for r in result["boxes"][2:]],
                                 ["WAIT","WAIT","WAIT"])
                self.assertEqual(result["historical_combined"]["coverage"],2)
                self.assertEqual(result["historical_combined"]["state"],"WAIT")
                self.assertEqual(result["combined"]["state"],"WAIT")
                self.assertTrue(all(not row["eligible_live"] for row in result["boxes"]))

    def test_no_history_or_wrong_source_never_invents_voting(self):
        for source,bars in (("Dhan",[]),("Yahoo Finance",completed_bars("1m"))):
            with self.subTest(source=source):
                r=historical_vote_replay(
                    symbol="NIFTY",timeframe="1m",generation=7,
                    source=source,bars=bars,filter_rows=[{"name":"EMA 9/21"}],
                    history_timestamp=HOLIDAY.timestamp())
                self.assertEqual(r["boxes"],[])
                self.assertEqual(r["historical_combined"]["state"],"WAIT")
                self.assertEqual(r["provider_requests"],0)

    def test_completed_historical_bar_with_afterhours_reference_is_not_live(self):
        rows=completed_bars("1m")
        reference=[int(datetime(2026,11,23,18,56,tzinfo=IST).timestamp()),
                   25000,25000,25000,25000,0]
        cleaned=historical_regular_session_bars(rows+[reference],"1m")
        self.assertEqual(cleaned,rows)
        self.assertEqual(analyze(cleaned,["EMA 9/21"],"1m")["count"],375)

    def test_selected_technical_and_independent_evidence_are_separate(self):
        self.assertIn("EMA 9/21",CANDLE_FILTERS)
        self.assertNotIn("News Headlines",CANDLE_FILTERS)
        self.assertNotIn("OI Support",CANDLE_FILTERS)

if __name__=="__main__":
    unittest.main()
