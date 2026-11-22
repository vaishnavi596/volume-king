"""Offline 5/34/54/70 market-capacity + HIST/LIVE safety gate.

Synthetic values measure pure local roster/state behavior; they are NOT
provider prices, exchange evidence, real mobile speed or certified LIVE data.
No Dhan/Oracle/Android/network calls and no order dispatch.
"""
import math
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from clone_smart_refresh_priority import (
    priority_equity_batch, auto_equity_quote_due, active_quote_view,
    accept_newer_dhan_quote, safe_quote_batch_for_cache,
)
from scanner_engine import ALL_FILTERS, OPTION_FILTERS
from filter_wiring_audit import filter_wiring_matrix
from analysis_reports import presentation_result, complete_filter_rows


class V3JointCapacityAndSessionGates(unittest.TestCase):
    def test_5_34_54_70_selected_equities_are_deduped_and_bounded(self):
        verified={"NIFTY","BANKNIFTY","SENSEX"}|{f"S{i:03d}" for i in range(1,81)}
        for count in (5,34,54,70):
            names=[f"S{i:03d}" for i in range(1,count+1)]
            duplicate_input=names+names[:min(12,count)]+["NIFTY","UNKNOWN"]
            positions=[names[-1],names[-1],names[0]]
            batch=priority_equity_batch(duplicate_input,positions,verified=verified)
            self.assertEqual(len(batch),count)
            self.assertEqual(len(set(batch)),count)
            self.assertNotIn("NIFTY",batch)
            self.assertNotIn("UNKNOWN",batch)
            self.assertEqual(batch[:2],[names[-1],names[0]])
            self.assertEqual(len(priority_equity_batch(duplicate_input,positions,
                verified=verified,limit=70)),count)
        capped=priority_equity_batch([f"S{i:03d}" for i in range(1,81)],
                                      [],verified=verified)
        self.assertEqual(len(capped),70)

    def test_no_quote_fanout_or_rollback_by_local_ui_clock(self):
        self.assertFalse(auto_equity_quote_due(122,100,floor_seconds=2))
        self.assertFalse(auto_equity_quote_due(159,100))
        self.assertTrue(auto_equity_quote_due(160,100))
        self.assertFalse(auto_equity_quote_due(161,100,busy=True))
        self.assertFalse(auto_equity_quote_due(90,100))
        self.assertEqual([active_quote_view(p) for p in range(6)],
                         [0,None,None,3,4,None])
        saved={"source":"Dhan","price":100.0,"quote_timestamp":1800000060}
        older={"source":"Dhan","price":99.0,"quote_timestamp":1800000000}
        self.assertFalse(accept_newer_dhan_quote(saved,older))
        self.assertFalse(accept_newer_dhan_quote(saved,{"source":"Dhan","price":101}))
        self.assertTrue(accept_newer_dhan_quote(saved,
            {"source":"Dhan","price":101,"quote_timestamp":1800000120}))
        for invalid in (True,0,-1,None,math.nan,math.inf):
            self.assertFalse(accept_newer_dhan_quote({},{"source":"Dhan","price":invalid}))

    def test_fresh_batch_cache_excludes_old_invalid_and_wrong_source(self):
        previous={"NIFTY":{"source":"Dhan","price":100,"quote_timestamp":1800000100},
                  "RELIANCE":{"source":"Dhan","price":200,"quote_timestamp":1800000200}}
        batch={"NIFTY":{"source":"Dhan","price":99,"quote_timestamp":1800000090},
               "RELIANCE":{"source":"Dhan","price":201,"quote_timestamp":1800000210},
               "TCS":{"source":"Dhan","price":90},
               "INFY":{"source":"Dhan","price":float("nan")},
               "YAHOO":{"source":"Yahoo Finance","price":250}}
        result=safe_quote_batch_for_cache(batch,previous,("NIFTY","RELIANCE","TCS","INFY","YAHOO"))
        self.assertEqual(set(result),{"RELIANCE","TCS"})
        self.assertEqual(result["RELIANCE"]["price"],201)
        self.assertEqual(previous["NIFTY"]["price"],100)
        self.assertEqual(safe_quote_batch_for_cache({},previous,previous),{})

    def test_market_close_hist_then_open_requires_new_verified_candle(self):
        base={"source":"Dhan","bias":"BULLISH","timestamp":1800000000,
              "freshness":"historical_unverified","historical":True,
              "live_verified":False,"votes":[{"name":"EMA 9/21","vote":1}]}
        history=presentation_result(base,expected_source="Dhan",now=1800000030,
            fresh_seconds=180,market_open=False)
        self.assertEqual(history["bias"],"BULLISH")
        self.assertEqual(history["actionable_bias"],"WAIT")
        self.assertFalse(history["live_verified"])
        # Market open and a recent clock alone do not make cached history LIVE.
        after_open=presentation_result(base,expected_source="Dhan",
            now=1800000040,fresh_seconds=180,market_open=True)
        self.assertEqual(after_open["display_state"],"HISTORICAL / UNVERIFIED")
        self.assertEqual(after_open["actionable_bias"],"WAIT")
        # The separate upstream verification contract can enable LIVE only
        # for a genuinely authenticated completed candle, never local repaint.
        proven=dict(base,historical=False,live_verified=True,
                    freshness="verified_live",cached=False)
        live=presentation_result(proven,expected_source="Dhan",
            now=1800000040,fresh_seconds=180,market_open=True)
        self.assertEqual(live["display_state"],"LIVE VERIFIED")
        self.assertEqual(live["actionable_bias"],"BULLISH")
        stale=presentation_result(proven,expected_source="Dhan",
            now=1800000700,fresh_seconds=180,market_open=True)
        self.assertFalse(stale["live_verified"])
        cross_source=presentation_result(proven,expected_source="Angel One",
            now=1800000040,fresh_seconds=180,market_open=True)
        self.assertEqual(cross_source["votes"],[])
        self.assertEqual(cross_source["bias"],"WAIT")

    def test_five_engine_closed_session_revokes_verified_live_display(self):
        source=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
        summary=source.split("    def five_engine_summary(",1)[1].split("    def five_engine_chips(",1)[0]
        chips=source.split("    def five_engine_chips(",1)[1].split("    def super_five_card(",1)[0]
        self.assertIn("if snapshot and not regular_hours():",summary)
        self.assertIn("if snapshot and not regular_hours():",chips)
        self.assertIn("snapshot=snapshot_for_display(None,now=time.time())",summary)
        self.assertIn("snapshot=snapshot_for_display(None,now=time.time())",chips)
        self.assertIn('historical_vote_agreement(shared_history(sym,"1m"),"1m")',chips)

    def test_unverified_1m_3m_summary_uses_matching_historical_cache(self):
        source=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
        summary=source.split("    def five_engine_summary(",1)[1].split("    def five_engine_chips(",1)[0]
        self.assertIn('if display_timeframe in ("1m","3m"):',summary)
        self.assertIn('selected_history=shared_history(symbol,display_timeframe)',summary)
        self.assertIn('historical_vote_agreement(selected_history,"1m")',summary)
        self.assertIn('signal_percentages(watch_three_minute_signal(symbol))',summary)
        self.assertIn('selected_history.get("_scanner_timeframe")==display_timeframe',summary)
        self.assertIn('valid_candle_history(selected_history.get("bars"))',summary)
        self.assertIn("0/5 LIVE verified",summary)
        self.assertNotIn('get_market_data(',summary)

    def test_disconnected_dhan_summary_keeps_historical_technical_only(self):
        source=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
        summary=source.split("    def five_engine_summary(",1)[1].split("    def five_engine_chips(",1)[0]
        self.assertIn('if prefs.get("source")=="Dhan" and display_timeframe in ("1m","3m"):',summary)
        self.assertIn("offline_history=shared_history(symbol,display_timeframe)",summary)
        self.assertIn('historical_vote_agreement(offline_history,"1m")',summary)
        self.assertIn("signal_percentages(watch_three_minute_signal(symbol))",summary)
        self.assertIn('"5 engines • OFFLINE • Technical HIST "',summary)
        self.assertIn('"% • LIVE 0/5 verified • N/F/O WAIT"',summary)
        self.assertNotIn('get_market_data(',summary)

    def test_historical_five_minute_summary_shared_with_chip_when_disconnected(self):
        source=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
        helper=source.split("    def historical_five_minute_technical(",1)[1].split("    def five_engine_summary(",1)[0]
        summary=source.split("    def five_engine_summary(",1)[1].split("    def five_engine_chips(",1)[0]
        self.assertIn('saved=watch_signal_cache.get(symbol) or {}',helper)
        self.assertIn('saved.get("timeframe")!="5m"',helper)
        self.assertIn('saved.get("source")!="Dhan"',helper)
        self.assertIn('counts=signal_percentages(saved)',helper)
        self.assertIn('historical_five_minute_technical(symbol)',summary)
        self.assertIn('"5 engines • OFFLINE • Technical HIST 5m B"',summary)
        self.assertIn('pieces[0]=("Technical HIST 5m B"',summary)
        self.assertIn('snapshot["engines"][0].display()["state"]=="WAIT"',summary)
        self.assertNotIn('get_market_data(',summary)

    def test_selected_18_filters_same_registry_but_missing_independent_vote(self):
        self.assertEqual(len(ALL_FILTERS),18)
        self.assertEqual(len(OPTION_FILTERS),4)
        technical=[n for n in ALL_FILTERS if n not in OPTION_FILTERS and n!="News Headlines"]
        self.assertEqual(len(technical),13)
        for sym in ("NIFTY","BANKNIFTY","SENSEX","RELIANCE"):
            self.assertTrue(sym)
            selected=list(ALL_FILTERS)
            actual=[{"name":n,"vote":0,"detail":"local neutral"} for n in technical]
            rows=complete_filter_rows({"votes":actual},selected)
            self.assertEqual(len(rows),18)
            diagnostic=filter_wiring_matrix(selected,rows,candle_ready=True,
                options_context=True,news_context=True)
            self.assertEqual([x["name"] for x in diagnostic],selected)
            self.assertEqual(sum(x["state"]=="CALCULATED" for x in diagnostic),13)
            self.assertEqual(sum(x["state"]=="ADAPTER_NOT_DIRECTIONAL" for x in diagnostic),5)
            self.assertTrue(all(x["vote"] is None
                for x in diagnostic if x["state"]!="CALCULATED"))


if __name__=="__main__":
    unittest.main()
