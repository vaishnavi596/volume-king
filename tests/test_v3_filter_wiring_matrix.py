"""Offline 18-filter wiring provenance and historical display regression."""
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from scanner_engine import ALL_FILTERS
from analysis_quality import candle_provenance_diagnostic
from filter_wiring_audit import filter_wiring_matrix, diagnostic_candle_readiness, doctor_filter_rows, has_recent_news_context, option_filter_context_readiness


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

    def test_candle_source_failure_does_not_mask_independent_context(self):
        selected=["Supertrend","OI Support","OI Resistance","Dhan Max Pain","News Headlines"]
        result=filter_wiring_matrix(selected,[],source="",
            candle_ready=False,options_context=True,news_context=False,
            timeframe="3m")
        self.assertEqual([row["state"] for row in result],
            ["SOURCE_MISMATCH","ADAPTER_NOT_DIRECTIONAL",
             "ADAPTER_NOT_DIRECTIONAL","ADAPTER_NOT_DIRECTIONAL",
             "NEWS_DATA_MISSING"])
        self.assertTrue(all(row["vote"] is None for row in result))
        absent=filter_wiring_matrix(selected,[],source="Dhan",
            candle_ready=False,options_context=False,news_context=True)
        self.assertEqual(absent[0]["state"],"CANDLE_DATA_MISSING_OR_INVALID")
        self.assertEqual(absent[1]["state"],"OPTION_DATA_MISSING")
        self.assertEqual(absent[-1]["state"],"ADAPTER_NOT_DIRECTIONAL")

    def test_normalized_digest_never_authenticates_raw_dhan(self):
        cases={"SHA256_MATCH":"NORMALIZED_GATEWAY_TO_PHONE_MATCH",
               "DERIVED_FROM_TRANSPORT_SHA256_MATCH":"DERIVED_FROM_NORMALIZED_MATCH_NOT_RAW",
               "RETAINED_DERIVED_HISTORY_UNVERIFIED":"RETAINED_HISTORICAL_NOT_CURRENT_TRANSPORT_PROOF",
               "NOT_PROVIDED":"NORMALIZED_TRANSPORT_UNVERIFIED"}
        for raw, expected in cases.items():
            diagnostic=candle_provenance_diagnostic(
                {"source":"Dhan","candle_transport_integrity":raw})
            self.assertEqual(diagnostic["transport"],expected)
            self.assertEqual(diagnostic["raw_dhan"],"UNVERIFIED")
            self.assertEqual(diagnostic["exchange_live"],"UNVERIFIED")
        mismatch=candle_provenance_diagnostic(
            {"source":"Angel One","candle_transport_integrity":"SHA256_MATCH"})
        self.assertEqual(mismatch["transport"],"SOURCE_MISSING_OR_MISMATCH")

    def test_option_readiness_is_expiry_and_filter_specific(self):
        from datetime import datetime,timezone
        now=datetime(2026,11,22,tzinfo=timezone.utc).timestamp()
        data={"source":"dhan","symbol":"NIFTY","expiry":"2026-11-26",
              "signal_eligible":False,"max_pain":25000}
        ready=option_filter_context_readiness(data,symbol="NIFTY",
            now=now,window_available=False)
        self.assertTrue(ready["Dhan Max Pain"])
        self.assertFalse(ready["OI Support"])
        self.assertFalse(ready["OI Profile"])
        self.assertFalse(option_filter_context_readiness(
            data,symbol="NIFTY",now=now,window_available=True)["OI Support"])
        valid_window={"available":True,"source":"Dhan",
            "freshness":"unverified","signal_eligible":False,"direction":"WAIT",
            "rows":tuple({"strike":25000+i*50,
                           "ce":{"oi":100.0},"pe":{"oi":200.0}}
                          for i in range(-3,4))}
        populated=option_filter_context_readiness(data,symbol="NIFTY",
            now=now,window_context=valid_window)
        self.assertTrue(all(populated.values()))
        truncated=option_filter_context_readiness(data,symbol="NIFTY",
            now=now,window_context=dict(valid_window,rows=valid_window["rows"][:3]))
        self.assertFalse(truncated["OI Profile"])
        self.assertTrue(truncated["Dhan Max Pain"])
        missing_leg=option_filter_context_readiness(data,symbol="NIFTY",
            now=now,window_context=dict(valid_window,rows=tuple(
                dict(row,ce={}) if i==0 else row
                for i,row in enumerate(valid_window["rows"]))))
        self.assertFalse(missing_leg["OI Resistance"])
        expired=option_filter_context_readiness(dict(data,expiry="2026-11-19"),
            symbol="NIFTY",now=now,window_context=valid_window)
        self.assertFalse(any(expired.values()))
        wrong=option_filter_context_readiness(data,symbol="BANKNIFTY",
            now=now,window_context=valid_window)
        self.assertFalse(any(wrong.values()))
        nonbroker=option_filter_context_readiness(dict(data,source="other"),
            symbol="NIFTY",now=now,window_context=valid_window)
        self.assertFalse(any(nonbroker.values()))
        matrix=filter_wiring_matrix(["OI Support","Dhan Max Pain"],[],
            options_context=ready)
        self.assertEqual([row["state"] for row in matrix],
            ["OPTION_DATA_MISSING","ADAPTER_NOT_DIRECTIONAL"])
        self.assertTrue(all(row["vote"] is None for row in matrix))

    def test_dhan_option_context_chain_to_doctor_never_votes(self):
        """Real 7-strike display adapter -> readiness -> matrix -> Doctor."""
        from datetime import datetime, timezone
        from five_engine import option_chain_display_context
        now=datetime(2026,11,22,tzinfo=timezone.utc).timestamp()
        rows=tuple({"strike":25000+i*50,
                    "ce":{"oi":120.0}, "pe":{"oi":90.0}}
                   for i in range(-3,4))
        metrics={"source":"dhan","symbol":"NIFTY","expiry":"2026-11-26",
                 "signal_eligible":False,"freshness":"unverified",
                 "max_pain":25000,
                 "atm_window":{"source":"dhan","freshness":"unverified",
                               "signal_eligible":False,"atm":25000,"rows":rows}}
        selected=("OI Support","OI Resistance","OI Profile","Dhan Max Pain")
        def diagnose(data):
            display=option_chain_display_context(data)
            readiness=option_filter_context_readiness(
                data,symbol="NIFTY",now=now,window_context=display)
            matrix=filter_wiring_matrix(selected,[],options_context=readiness,
                                        candle_ready=False)
            doctor=doctor_filter_rows(
                [{"filter":name,"detail":"source context"} for name in selected],
                matrix)
            return display,readiness,matrix,doctor

        display,ready,matrix,doctor=diagnose(metrics)
        self.assertTrue(display["available"])
        self.assertTrue(all(ready.values()))
        self.assertEqual([r["status"] for r in doctor],["CONTEXT_ONLY"]*4)
        self.assertTrue(all(r["vote"] is None for r in matrix))

        # A duplicated strike or wrong center ATM is rejected by the actual
        # display adapter, not merely a synthetic readiness hint.
        duplicate=tuple(dict(row,strike=25000) if i==4 else row
                        for i,row in enumerate(rows))
        invalids=(
            dict(metrics,atm_window=dict(metrics["atm_window"],rows=duplicate)),
            dict(metrics,atm_window=dict(metrics["atm_window"],atm=25050)),
            dict(metrics,atm_window=dict(metrics["atm_window"],rows=rows[:6])),
            dict(metrics,expiry="2026-11-19"),
            dict(metrics,source="Yahoo"),
            dict(metrics,signal_eligible=True),
        )
        for bad in invalids:
            with self.subTest(cause=str(bad.get("source"))+" / "+str(bad.get("expiry"))):
                display,ready,matrix,doctor=diagnose(bad)
                self.assertFalse(any(ready[name] for name in
                                 ("OI Support","OI Resistance","OI Profile")))
                self.assertEqual([r["status"] for r in doctor[:3]],["WAIT"]*3)
                self.assertTrue(all(r["vote"] is None for r in matrix))
        # Even a complete, valid option chain cannot fabricate LIVE direction.
        self.assertFalse(any(x["vote"] is not None for x in matrix))

    def test_news_readiness_excludes_undated_old_and_future_headlines(self):
        now=1800000000
        article={"title":"Dhan market company item","published":now-90}
        context={"fetched":now-30,"items":[article]}
        self.assertTrue(has_recent_news_context(context,now=now))
        self.assertFalse(has_recent_news_context({"fetched":now-90000,"items":[article]},now=now))
        self.assertFalse(has_recent_news_context({"fetched":now-30,"items":[{"title":"old","published":now-90000}]},now=now))
        self.assertFalse(has_recent_news_context({"fetched":now-30,"items":[{"title":"undated"}]},now=now))
        self.assertFalse(has_recent_news_context({"fetched":now-30,"items":[{"title":"future","published":now+300}]},now=now))
        self.assertFalse(has_recent_news_context({"fetched":now-30,"items":[article]},now=now+90000))

    def test_invalid_candles_cannot_pretend_to_vote(self):
        result=filter_wiring_matrix(["Supertrend"],[{"name":"Supertrend","vote":1}],
                                   candle_ready=False)
        self.assertEqual(result[0]["state"],"CANDLE_DATA_MISSING_OR_INVALID")
        self.assertIsNone(result[0]["vote"])

    def test_doctor_labels_use_wiring_not_message_word_guess(self):
        selected=["RSI 14","OI Support","News Headlines"]
        rows=[{"filter":"RSI 14","status":"BULLISH","detail":"stale value"},
              {"filter":"OI Support","status":"WAIT","detail":"source ready"},
              {"filter":"News Headlines","status":"WAIT","detail":"six headlines"}]
        matrix=filter_wiring_matrix(selected,[{"name":"RSI 14","vote":1}],
            source="Dhan",candle_ready=False,options_context=True,news_context=True)
        result=doctor_filter_rows(rows,matrix)
        self.assertEqual([r["status"] for r in result],["WAIT","CONTEXT_ONLY","CONTEXT_ONLY"])
        self.assertEqual(result[0]["stage"],"CANDLE_DATA_MISSING_OR_INVALID")
        self.assertEqual(result[1]["stage"],"INDEPENDENT_CONTEXT_NO_DIRECTIONAL_VOTE")
        matrix2=filter_wiring_matrix(selected,[{"name":"RSI 14","vote":-1}],
            source="Dhan",candle_ready=True,options_context=False,news_context=False)
        result2=doctor_filter_rows(rows,matrix2)
        self.assertEqual([r["status"] for r in result2],["BEARISH","WAIT","WAIT"])

    def test_candle_readiness_requires_exact_timeframe_and_completed_bar(self):
        bars=[[1800000000+i*60,100,101,99,100,12] for i in range(30)]
        historical={"source":"Dhan","_scanner_timeframe":"1m","bars":bars}
        self.assertEqual(diagnostic_candle_readiness(historical,"1m",
            now=1800000000+30*60),"READY_FOR_QUALITY_AND_CALCULATION")
        self.assertEqual(diagnostic_candle_readiness(historical,"3m",
            now=1800000000+30*60),"TIMEFRAME_MISMATCH")
        self.assertEqual(diagnostic_candle_readiness(historical,"1m",
            now=1800000000+29*60),"LATEST_CANDLE_NOT_COMPLETED")
        self.assertEqual(diagnostic_candle_readiness(
            {"source":"Yahoo Finance",**{"bars":bars,"_scanner_timeframe":"1m"}},
            "1m",now=1800000000+30*60),"SOURCE_MISSING_OR_MISMATCH")
        self.assertEqual(diagnostic_candle_readiness(
            {"source":"Dhan","_scanner_timeframe":"1m","bars":bars[:3]},
            "1m",now=1800000000+30*60),"CANDLE_DATA_MISSING_OR_INSUFFICIENT")

    def test_diagnostic_same_timeframe_gates_evidence(self):
        src=(ROOT/"src/main.py").read_text(encoding="utf-8")
        import ast
        tree=ast.parse(src)
        nodes=[node for node in ast.walk(tree)
               if isinstance(node,ast.FunctionDef)
               and node.name=="filter_five_diagnostic_panel"]
        self.assertEqual(len(nodes),1)
        block=ast.get_source_segment(src,nodes[0])
        self.assertIn("diagnostic_candle_readiness(history,tf,now=time.time())",block)
        self.assertIn('selected_candle_readiness',block)
        self.assertIn('doctor_filter_rows(filter_rows,wiring_matrix)',block)
        self.assertIn('has_recent_news_context(news_context,now=time.time())',block)
        self.assertIn('option_filter_context_readiness(',block)
        self.assertIn('candle_provenance_diagnostic(history)',block)
        self.assertIn('"candle_provenance_verdict":provenance',block)
        self.assertIn('tf=="5m" and prefs.get("source")=="Dhan"',block)
        self.assertIn('"engine_snapshot_present":(tf=="5m" and symbol in five_engine_snapshots)',block)
        self.assertIn('prepared_snapshot=(five_engine_snapshots.get(symbol)',block)
        self.assertIn('result.get("count",0)>=30',block)

    def test_scanner_doctor_disallows_foreign_timeframe_engine_evidence(self):
        src=(ROOT/"src/main.py").read_text(encoding="utf-8")
        doctor=src.split("                scanner_sym=str(scan_symbol.value or",1)[1]
        doctor=doctor.split("                sections={",1)[0]
        self.assertIn('scanner_engine_5m_eligible=(scanner_tf=="5m"',doctor)
        self.assertIn('read_five_engine_context(scanner_sym,"5m")',doctor)
        self.assertIn('and regular_hours())',doctor)
        self.assertIn('if scanner_engine_5m_eligible else None)',doctor)
        self.assertIn('if scanner_engine_5m_eligible else None)',doctor.split('raw=(next(',1)[1])
        self.assertNotIn('if prefs.get("source")=="Dhan" and dhan_feed.connected else None)',doctor)

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
