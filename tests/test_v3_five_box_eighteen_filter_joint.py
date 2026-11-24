"""Joint 18-filter × five-engine HIST regression; synthetic OHLCV test fixture ONLY.

No broker requests, no market-live claims, no Oracle deployment and no orders.
This is one gate across all source lanes, not 18 independent data engines.
"""
import pathlib
import sys
import unittest
from datetime import datetime, timedelta, timezone

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from scanner_engine import ALL_FILTERS, OPTION_FILTERS, analyze
from filter_wiring_audit import CANDLE_FILTERS, filter_wiring_matrix
from five_engine import ENGINE_NAMES
from v3_historical_vote_replay import historical_vote_replay
from v3_four_box_source_readiness import four_box_source_readiness

IST=timezone(timedelta(hours=5,minutes=30))


def completed_fixture(timeframe):
    seconds={"1m":60,"3m":180,"5m":300}[timeframe]
    start=int(datetime(2026,11,23,9,15,tzinfo=IST).timestamp())
    bars=[]
    for i in range(60):
        p=25000 + (i//4)*2 + (i%4)*0.25
        bars.append([start+i*seconds,p,p+2,p-2,p+1 if i%3 else p-1,100+i])
    return bars


class JointFiveBoxesEighteenFilters(unittest.TestCase):
    def test_display_summary_must_not_borrow_five_minute_hist_for_1m_or_3m(self):
        """Reject cross-timeframe fallback even when LIVE technical is WAIT.

        The exact-frame 1m/3m source may supply HIST on its own, but a
        published 5m ranking cannot be relabeled as their T display.
        """
        from textwrap import dedent
        source=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
        summary=source.split("    def five_engine_summary(",1)[1].split(
            "    def five_engine_chips(",1)[0]
        self.assertIn(
            'if exact_frame=="5m" and snapshot["engines"][0].display()["state"]=="WAIT":',
            summary)
        self.assertEqual(summary.count("last_votes=historical_five_minute_technical(symbol)"),2)
        self.assertIn('if prefs.get("source")=="Dhan" and display_timeframe in (None,"5m"):',summary)
        self.assertIn('exact_frame=display_timeframe or "5m"',summary)

    def test_shared_phone_vote_display_rejects_context_and_duplicate_integers(self):
        # Execute the actual application function isolated from app_main,
        # detecting cross-lane B/S inflation in saved/restored reports.
        import ast
        source=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
        tree=ast.parse(source)
        matches=[node for node in ast.walk(tree)
                 if isinstance(node,ast.FunctionDef)
                 and node.name=="signal_percentages"]
        self.assertEqual(len(matches),1)
        scope={}
        exec(compile(ast.Module(body=[matches[0]],type_ignores=[]),
                     "<v3-shared-filter-vote>", "exec"),scope)
        count=scope["signal_percentages"]
        clean=[{"name":"Supertrend","vote":1},
               {"name":"EMA 9/21","vote":1},
               {"name":"MACD","vote":-1}]
        forged=clean+[
            {"name":"OI Support","vote":1},
            {"name":"OI Resistance","vote":1},
            {"name":"OI Profile","vote":1},
            {"name":"Dhan Max Pain","vote":1},
            {"name":"News Headlines","vote":1},
            {"name":"unknown","vote":1},
            {"name":"Supertrend","vote":1},
            {"name":"RSI 14","vote":True},
        ]
        self.assertEqual(count({"votes":clean}),(67,33,3))
        self.assertEqual(count({"votes":forged}),count({"votes":clean}))
        self.assertIsNone(count({"votes":forged[len(clean):len(clean)+6]}))
        self.assertEqual(count({"votes":[{"name":"Supertrend","vote":1},
                                         {"name":"Supertrend","vote":1}]}),(100,0,1))
        self.assertIsNone(count({"votes":[]}))
        self.assertEqual(count({"votes":clean[0:2]}),(100,0,2))

    def test_all_v3_surfaces_share_readonly_canonical_live_final_presenter(self):
        """No 1m/3m/5m source relabel and no separate voting policy per screen."""
        from test_audit import start
        source=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
        self.assertIn('canonical_live_final_note(index_name,"1m")',source)
        self.assertIn('canonical_live_final_note(sym,"1m")',source)
        self.assertIn('canonical_live_final_note(sym,"3m")',source)
        self.assertIn('canonical_live_final_note(row["symbol"],"5m")',source)
        self.assertIn('canonical_live_final_note(scan_symbol.value or "NIFTY",scan_tf.value)',source)
        _,views=start({"source":"Dhan","scanner_live":False})
        status=views["canonical_live_final_note"]("NIFTY","1m").value
        self.assertIn("LIVE FINAL • WAIT",status)
        self.assertIn("0/5 verified",status)
        self.assertIn("market closed or Dhan disconnected",status)
        self.assertIn("unsupported timeframe",
                      views["canonical_live_final_note"]("NIFTY","2m").value)

    def test_canonical_eighteen_registry_and_exact_five_lanes(self):
        self.assertEqual(len(ALL_FILTERS),18)
        self.assertEqual(len(set(ALL_FILTERS)),18)
        self.assertEqual(len(CANDLE_FILTERS),13)
        self.assertEqual(len(OPTION_FILTERS),4)
        self.assertEqual(set(ALL_FILTERS)-set(CANDLE_FILTERS)-set(OPTION_FILTERS),
                         {"News Headlines"})
        self.assertEqual(ENGINE_NAMES,
                         ("technical","candle","news","futures","options"))

    def test_all_eighteen_scanner_filters_and_five_boxes_each_frame(self):
        for frame,seconds in (("1m",60),("3m",180),("5m",300)):
            with self.subTest(timeframe=frame):
                bars=completed_fixture(frame)
                before=[b[:] for b in bars]
                scan=analyze(bars,selected=list(ALL_FILTERS),timeframe=frame)
                self.assertEqual(scan["count"],60)
                self.assertEqual(scan["timestamp"],bars[-1][0])
                self.assertEqual(set(v["name"] for v in scan["votes"]),set(ALL_FILTERS))
                self.assertTrue(all(
                    row["vote"] is None for row in scan["votes"]
                    if row["name"] in OPTION_FILTERS or row["name"]=="News Headlines"))
                wire=filter_wiring_matrix(
                    ALL_FILTERS,scan["votes"],source="Dhan",
                    timeframe=frame,candle_ready=True,
                    options_context=False,news_context=False)
                self.assertEqual(len(wire),18)
                self.assertTrue(all(
                    row["state"] in ("OPTION_DATA_MISSING","NEWS_DATA_MISSING")
                    for row in wire if row["name"] in OPTION_FILTERS
                    or row["name"]=="News Headlines"))
                replay=historical_vote_replay(
                    symbol="NIFTY",timeframe=frame,generation=7,
                    source="Dhan",bars=bars,filter_rows=scan["votes"],
                    history_timestamp=bars[-1][0]+seconds)
                self.assertEqual([box["engine"] for box in replay["boxes"]],
                                 list(ENGINE_NAMES))
                self.assertEqual([box["state"] for box in replay["boxes"]][2:],
                                 ["WAIT","WAIT","WAIT"])
                self.assertEqual(replay["boxes"][0]["state"],"HIST_VOTE")
                self.assertEqual(replay["boxes"][1]["state"],"HIST_VOTE")
                self.assertEqual(replay["combined"]["state"],"WAIT")
                self.assertEqual(replay["combined"]["coverage"],2)
                self.assertEqual(replay["provider_requests"],0)
                self.assertEqual(replay["orders_sent"],0)
                self.assertFalse(replay["verified_live"])
                self.assertEqual(bars,before)

    def test_doctor_joint_18_filters_four_context_sources_each_frame(self):
        for frame,sec in (("1m",60),("3m",180),("5m",300)):
            with self.subTest(frame=frame):
                bars=completed_fixture(frame)
                futures=dict(source="Dhan",symbol="NIFTY",underlying="NIFTY",
                             exchange_segment="NSE_FNO",expiry="2026-12-31",
                             contract="NIFTY DEC FUT",ltp=25200.0,
                             mapping_verified=True,freshness="unverified",
                             direction=None,direction_verified=False,
                             signal_eligible=False,live_orders_enabled=False)
                report=four_box_source_readiness(
                    symbol="NIFTY",timeframe=frame,generation=7,
                    history={"source":"Dhan","_scanner_timeframe":frame,"bars":bars},
                    news_cache={"items":[{"title":"Context",
                                          "url":"https://example.org/context",
                                          "source":"RSS Publisher",
                                          "published":bars[-1][0]}]},
                    futures_cache=futures,
                    option_context={"source":"dhan","symbol":"NIFTY",
                                    "expiry":"2026-12-31","signal_eligible":False},
                    now=bars[-1][0]+sec)
                self.assertEqual(set(report["box_sources"]),{"C","N","F","O"})
                self.assertTrue(report["box_sources"]["C"]["historical_direction_available"])
                self.assertTrue(all(report["box_sources"][key]["cache_present"]
                                    for key in ("N","F","O")))
                self.assertEqual(report["live_vote_count"],0)
                self.assertTrue(all(not row["live_direction_verified"]
                                    for row in report["box_sources"].values()))
                self.assertEqual(report["provider_requests"],0)
                self.assertEqual(report["orders_sent"],0)

    def test_user_seventeen_filter_selection_does_not_invent_sixth_or_votes(self):
        # User may choose 17/18. Preserve exactly the chosen registry rows.
        selected=[name for name in ALL_FILTERS if name!="News Headlines"]
        self.assertEqual(len(selected),17)
        for frame,seconds in (("1m",60),("3m",180),("5m",300)):
            with self.subTest(frame=frame):
                candles=completed_fixture(frame)
                scan=analyze(candles,selected=selected,timeframe=frame)
                self.assertEqual(len(scan["votes"]),17)
                self.assertEqual(set(row["name"] for row in scan["votes"]),set(selected))
                matrix=filter_wiring_matrix(
                    selected,scan["votes"],source="Dhan",timeframe=frame,
                    candle_ready=True,options_context=False,news_context=False)
                self.assertEqual(len(matrix),17)
                replay=historical_vote_replay(
                    symbol="NIFTY",timeframe=frame,generation=9,
                    source="Dhan",bars=candles,filter_rows=scan["votes"],
                    history_timestamp=candles[-1][0]+seconds)
                self.assertEqual(len(replay["boxes"]),5)
                self.assertEqual([box["engine"] for box in replay["boxes"]],
                                 list(ENGINE_NAMES))
                self.assertEqual([box["state"] for box in replay["boxes"]][2:],
                                 ["WAIT","WAIT","WAIT"])
                self.assertEqual(replay["combined"]["state"],"WAIT")
                self.assertEqual(replay["provider_requests"],0)
                self.assertEqual(replay["orders_sent"],0)

    def test_injected_news_and_option_integers_cannot_change_live_T(self):
        from five_engine import scanner_snapshot
        for frame in ("1m","3m","5m"):
            with self.subTest(frame=frame):
                scan={"votes":[{"name":"EMA 9/21","vote":1},
                               {"name":"RSI 14","vote":1},
                               {"name":"MACD","vote":-1}],
                      "source":"Dhan","timestamp":1795000000,
                      "timeframe":frame,"live_verified":True,
                      "freshness":"verified_live","historical":False}
                clean=scanner_snapshot(scan)
                polluted=dict(scan,votes=scan["votes"]+[
                    {"name":name,"vote":1} for name in OPTION_FILTERS
                ]+[{"name":"News Headlines","vote":-1}])
                actual=scanner_snapshot(polluted)
                self.assertEqual(actual["engines"][0],clean["engines"][0])
                self.assertEqual((actual["engines"][0].bullish,
                                  actual["engines"][0].bearish),(67,33))
                self.assertEqual(actual["combined"]["coverage"],1)
                self.assertEqual(actual["combined"]["state"],"WAIT")
                self.assertTrue(all(not e.eligible for e in actual["engines"][1:]))

    def test_independent_context_integer_cannot_create_technical_quorum(self):
        from five_engine import scanner_snapshot
        scan={"votes":[{"name":"MACD","vote":1},
                       {"name":"OI Support","vote":1},
                       {"name":"OI Resistance","vote":1},
                       {"name":"News Headlines","vote":1}],
              "source":"Dhan","timestamp":1795000000,
              "live_verified":True,"freshness":"verified_live",
              "historical":False}
        result=scanner_snapshot(scan)
        self.assertEqual(result["combined"]["coverage"],0)
        self.assertEqual(result["combined"]["state"],"WAIT")
        self.assertFalse(result["engines"][0].eligible)

    def test_options_measured_strength_must_agree_with_claimed_bias(self):
        from five_engine import option_from_component, compose_snapshot, EngineEvidence
        good=dict(available=True,source="Dhan",verified=True,
                  direction_basis="validated_trade_flow",
                  contract="NIFTY-CE",timestamp=1795000000,
                  bullish=85,bearish=15,bias="BULLISH")
        good_result=option_from_component(good)
        self.assertTrue(good_result.eligible)
        self.assertEqual((good_result.bullish,good_result.bearish),(85,15))
        for conflict in (
            dict(good,bias="BEARISH"),
            dict(good,bullish=15,bearish=85),
            dict(good,bullish=50,bearish=50)):
            with self.subTest(conflict=conflict):
                output=option_from_component(conflict)
                self.assertFalse(output.eligible)
                self.assertEqual(output.display()["state"],"WAIT")
                self.assertIn("conflicts",output.reason)
                combined=compose_snapshot(options=output)
                self.assertEqual(combined["combined"]["coverage"],0)
        reverse=option_from_component(dict(good,bias="BEARISH",
                                           bullish=15,bearish=85))
        self.assertTrue(reverse.eligible)
        self.assertEqual(reverse.display()["state"],"BEARISH")

    def test_option_expiry_when_supplied_must_be_valid_at_evidence_time(self):
        from datetime import datetime,timezone,timedelta
        from five_engine import option_from_component
        ist=timezone(timedelta(hours=5,minutes=30))
        stamp=int(datetime(2026,11,24,14,20,tzinfo=ist).timestamp())
        sample=dict(source="Dhan",available=True,verified=True,
                    contract="NIFTY-CE",direction_basis="validated_trade_flow",
                    bias="BULLISH",bullish=75,bearish=25,timestamp=stamp)
        for expiry in ("2026-11-24","2026-11-26"):
            self.assertTrue(option_from_component(dict(sample,expiry=expiry)).eligible)
        for expiry in ("2026-11-23","2026-11-24T00:00:00",
                       "2026-11-24xyz",True,""):
            with self.subTest(expiry=expiry):
                bad=option_from_component(dict(sample,expiry=expiry))
                self.assertFalse(bad.eligible)
                self.assertEqual(bad.display()["state"],"WAIT")
        # An absent expiry is retained as a legacy adapter contract, but
        # does not itself assert that the provider populated a current expiry.
        self.assertTrue(option_from_component(sample).eligible)

    def test_no_legacy_context_can_promote_news_futures_options(self):
        bars=completed_fixture("1m")
        raw=analyze(bars,selected=ALL_FILTERS,timeframe="1m")
        contaminated=[
            dict(row,vote=1) if row["name"] in OPTION_FILTERS
            or row["name"]=="News Headlines" else dict(row)
            for row in raw["votes"]]
        clean=historical_vote_replay(
            symbol="NIFTY",timeframe="1m",generation=7,source="Dhan",
            bars=bars,filter_rows=raw["votes"],history_timestamp=bars[-1][0]+60)
        polluted=historical_vote_replay(
            symbol="NIFTY",timeframe="1m",generation=7,source="Dhan",
            bars=bars,filter_rows=contaminated,
            history_timestamp=bars[-1][0]+60)
        self.assertEqual(polluted["technical_vote"],clean["technical_vote"])
        self.assertEqual([x["state"] for x in polluted["boxes"]][2:],
                         ["WAIT","WAIT","WAIT"])
        self.assertFalse(polluted["verified_live"])
        self.assertEqual(polluted["orders_sent"],0)


if __name__=="__main__":
    unittest.main()
