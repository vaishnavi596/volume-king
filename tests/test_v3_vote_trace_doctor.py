"""Ensure phone Doctor identifies calculation, vote and final display gaps."""
import ast
import pathlib
import sys
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from v3_vote_trace_doctor import audit_vote_trace
from five_engine import EngineEvidence,compose_snapshot
from scanner_engine import ALL_FILTERS,OPTION_FILTERS
from filter_wiring_audit import CANDLE_FILTERS

def boxes():
    return [{"engine":n,"status":"WAIT","raw_verified":False,
             "blocker":"UNVERIFIED"} for n in
            ("technical","candle","news","futures","options")]
def base(**changes):
    params=dict(symbol="NIFTY",timeframe="1m",generation=1,
                filter_rows=[{"name":"EMA 9/21","vote":1,"status":"BULLISH"},
                             {"name":"RSI 14","vote":0,"status":"NEUTRAL"},
                             {"name":"OI Support","vote":None,"status":"CONTEXT_ONLY"}],
                box_rows=boxes(),market_open=False)
    params.update(changes)
    return audit_vote_trace(**params)

class VoteTraceDoctorTests(unittest.TestCase):
    def test_actual_voting_is_not_invented_on_market_close(self):
        r=base()
        self.assertEqual(r["filter_calculation"]["selected"],3)
        self.assertEqual(r["filter_calculation"]["calculated"],2)
        self.assertEqual(r["filter_calculation"]["directional"],1)
        self.assertEqual(r["filter_calculation"]["neutral"],1)
        self.assertEqual(r["filter_calculation"]["context_only"],1)
        self.assertEqual(r["box_vote_gate"]["eligible"],0)
        self.assertEqual(r["box_vote_gate"]["sixth_M"],"STANDBY_NOT_SCORED")
        self.assertEqual(r["combined_vote"]["state"],"WAIT")
        self.assertTrue(r["combined_vote"]["historical_filter_agreement_is_separate"])
        self.assertEqual(r["provider_requests"],0)
        self.assertEqual(r["orders_sent"],0)
    def test_three_valid_engines_only_if_full_provenance_present(self):
        rows=boxes()
        source=[]
        for i,n in enumerate(("technical","candle","news","futures","options")):
            yes=i<3
            source.append(EngineEvidence(n,70 if yes else None,30 if yes else None,
                                         verified=yes,timestamp=1795000000 if yes else None,
                                         source="Dhan" if yes else ""))
            if yes:
                rows[i].update(status="BULLISH",raw_verified=True,raw_source="Dhan",
                               bullish_percent=70,bearish_percent=30)
        snap=compose_snapshot(**dict(zip(("technical","candle","news","futures","options"),source)))
        r=base(market_open=True,box_rows=rows,snapshot=snap)
        self.assertEqual(r["combined_vote"]["state"],"BULLISH")
        self.assertEqual(r["combined_vote"]["coverage"],3)
        self.assertEqual(r["box_vote_gate"]["eligible"],3)
        self.assertEqual(base(box_rows=rows,snapshot=snap)["combined_vote"]["state"],"WAIT")
    def test_forged_display_percent_cannot_attest_published_engine(self):
        rows=boxes()
        source=[]
        for i,n in enumerate(("technical","candle","news","futures","options")):
            yes=i<3
            source.append(EngineEvidence(n,70 if yes else None,30 if yes else None,
                                         verified=yes,timestamp=1795000000 if yes else None,
                                         source="Dhan" if yes else ""))
            if yes:
                rows[i].update(status="BULLISH",raw_verified=True,raw_source="Dhan",
                               bullish_percent=70,bearish_percent=30)
        snapshot=compose_snapshot(**dict(zip(("technical","candle","news","futures","options"),source)))
        rows[2]["bullish_percent"]=80
        rows[2]["bearish_percent"]=20
        result=base(market_open=True,box_rows=rows,snapshot=snapshot)
        self.assertEqual(result["box_vote_gate"]["eligible"],2)
        self.assertEqual(result["box_vote_gate"]["boxes"][2]["vote_state"],"BLOCKED")
        self.assertEqual(result["combined_vote"]["state"],"WAIT")
        self.assertEqual(result["combined_vote"]["reason"],"DISPLAY_SIDE_PROVENANCE_NOT_VERIFIED")
        self.assertEqual(result["provider_requests"],0)
        self.assertEqual(result["orders_sent"],0)

    def test_display_direction_must_agree_with_verified_percentages(self):
        rows=boxes()
        engine_names=("technical","candle","news","futures","options")
        evidence=[]
        for i,n in enumerate(engine_names):
            valid=i<3
            evidence.append(EngineEvidence(n,70 if valid else None,30 if valid else None,
                                           verified=valid,timestamp=1795000000 if valid else None,
                                           source="Dhan" if valid else ""))
            if valid:
                rows[i].update(status="BULLISH",raw_verified=True,raw_source="Dhan",
                               bullish_percent=70,bearish_percent=30)
        rows[2]["status"]="BEARISH"  # percentages stay 70/30, direction is forged
        snapshot=compose_snapshot(**dict(zip(engine_names,evidence)))
        result=base(market_open=True,box_rows=rows,snapshot=snapshot)
        self.assertEqual(result["box_vote_gate"]["eligible"],2)
        self.assertEqual(result["box_vote_gate"]["boxes"][2]["vote_state"],"BLOCKED")
        self.assertEqual(result["combined_vote"]["state"],"WAIT")
        self.assertEqual(result["provider_requests"],0)
        self.assertEqual(result["orders_sent"],0)

    def test_published_combined_mismatch_blocks_final_trace_vote(self):
        rows=boxes()
        names=("technical","candle","news","futures","options")
        evidence=[]
        for i,name in enumerate(names):
            verified=i<3
            evidence.append(EngineEvidence(name,70 if verified else None,
                                           30 if verified else None,verified=verified,
                                           timestamp=1795000000 if verified else None,
                                           source="Dhan" if verified else ""))
            if verified:
                rows[i].update(status="BULLISH",raw_verified=True,raw_source="Dhan",
                               bullish_percent=70,bearish_percent=30)
        snapshot=compose_snapshot(**dict(zip(names,evidence)))
        self.assertEqual(snapshot["combined"]["state"],"BULLISH")
        snapshot["combined"]=dict(snapshot["combined"],state="BEARISH")
        result=base(market_open=True,box_rows=rows,snapshot=snapshot)
        self.assertEqual(result["box_vote_gate"]["eligible"],3)
        self.assertEqual(result["voting_conflict_audit"]["issues"][0]["code"],
                         "COMBINED_VOTE_PUBLISH_MISMATCH")
        self.assertEqual(result["combined_vote"]["state"],"WAIT")
        self.assertEqual(result["combined_vote"]["reason"],"COMBINED_VOTE_PUBLISH_MISMATCH")
        self.assertIsNone(result["combined_vote"]["bullish"])
        self.assertEqual(result["provider_requests"],0)
        self.assertEqual(result["orders_sent"],0)

    def test_missing_published_combined_never_becomes_live_vote(self):
        names=("technical","candle","news","futures","options")
        rows=boxes()
        evidence=[]
        for i,name in enumerate(names):
            active=i<3
            evidence.append(EngineEvidence(name,70 if active else None,
                                           30 if active else None,verified=active,
                                           timestamp=1795000000 if active else None,
                                           source="Dhan" if active else ""))
            if active:
                rows[i].update(status="BULLISH",raw_verified=True,raw_source="Dhan",
                               bullish_percent=70,bearish_percent=30)
        result=base(market_open=True,box_rows=rows,snapshot={"engines":tuple(evidence)})
        self.assertEqual(result["box_vote_gate"]["eligible"],3)
        self.assertEqual(result["combined_vote"]["state"],"WAIT")
        self.assertEqual(result["combined_vote"]["reason"],"PUBLISHED_COMBINED_VOTE_MISSING")
        self.assertIsNone(result["combined_vote"]["bullish"])
        self.assertEqual(result["provider_requests"],0)
        self.assertEqual(result["orders_sent"],0)

    def test_missing_display_proof_does_not_turn_three_engine_snapshot_live(self):
        a=tuple(EngineEvidence(n,70 if i<3 else None,30 if i<3 else None,
                       verified=i<3,timestamp=1795000000 if i<3 else None,
                       source="Dhan" if i<3 else "")
                       for i,n in enumerate(("technical","candle","news","futures","options")))
        r=base(snapshot={"engines":a},market_open=True)
        self.assertEqual(r["combined_vote"]["state"],"WAIT")
        self.assertEqual(r["combined_vote"]["reason"],"PUBLISHED_COMBINED_VOTE_MISSING")
    def test_duplicate_filter_and_box_rejected(self):
        with self.assertRaises(ValueError):
            base(filter_rows=[{"name":"EMA 9/21"},{"name":"EMA 9/21"}])
        with self.assertRaises(ValueError):
            base(box_rows=boxes()[:-1]+[boxes()[0]])
    def test_context_vote_injection_never_inflates_technical_counts(self):
        rows=[{"name":name,"vote":1,"status":"BULLISH"} for name in ALL_FILTERS]
        result=base(filter_rows=rows)
        c=result["filter_calculation"]
        self.assertEqual(c["selected"],18)
        self.assertEqual(c["calculated"],len(CANDLE_FILTERS))
        self.assertEqual(c["directional"],len(CANDLE_FILTERS))
        self.assertEqual(c["context_only"],len(OPTION_FILTERS)+1)
        self.assertEqual(c["errors"],0)
        self.assertEqual(result["box_vote_gate"]["eligible"],0)
        self.assertEqual(result["box_vote_gate"]["sixth_M"],"STANDBY_NOT_SCORED")
        self.assertEqual(result["combined_vote"]["state"],"WAIT")
        reasons={row["name"]:row["stage"] for row in c["blocked_details"]}
        self.assertEqual(reasons["News Headlines"],"NEWS_CONTEXT_NOT_INDEPENDENT_VOTE")
        self.assertEqual(reasons["Dhan Max Pain"],"OPTION_CONTEXT_NOT_INDEPENDENT_VOTE")

    def test_17_selected_and_18_registered_all_three_timeframes(self):
        for frame in ("1m","3m","5m"):
            for choice in (ALL_FILTERS,ALL_FILTERS[:-1]):
                with self.subTest(frame=frame,count=len(choice)):
                    rows=[{"name":name,"vote":1,"status":"BULLISH"} for name in choice]
                    result=audit_vote_trace(
                        symbol="NIFTY",timeframe=frame,generation=7,
                        filter_rows=rows,box_rows=boxes(),market_open=False)
                    counts=result["filter_calculation"]
                    self.assertEqual(counts["selected"],len(choice))
                    self.assertEqual(counts["calculated"],13)
                    self.assertEqual(counts["context_only"],len(choice)-13)
                    self.assertEqual(result["box_vote_gate"]["eligible"],0)
                    self.assertEqual(len(result["box_vote_gate"]["boxes"]),5)
                    self.assertEqual(result["box_vote_gate"]["sixth_M"],"STANDBY_NOT_SCORED")
                    self.assertEqual(result["combined_vote"]["state"],"WAIT")
                    self.assertEqual(result["provider_requests"],0)
                    self.assertEqual(result["orders_sent"],0)

    def test_unknown_and_wait_or_chart_votes_cannot_cast_technical_vote(self):
        rows=[{"name":"Unlisted Technical","vote":1,"status":"BULLISH"},
              {"name":"EMA 9/21","vote":1,"status":"WAIT"},
              {"name":"RSI 14","vote":-1,"status":"CHART_ONLY"},
              {"name":"News Headlines","vote":1,"status":"BULLISH"}]
        result=base(filter_rows=rows)
        counts=result["filter_calculation"]
        self.assertEqual(counts["selected"],4)
        self.assertEqual(counts["calculated"],0)
        self.assertEqual(counts["directional"],0)
        self.assertEqual(counts["context_only"],1)
        self.assertEqual(counts["errors"],1)
        self.assertEqual(counts["waiting"],2)
        self.assertEqual(result["combined_vote"]["state"],"WAIT")

    def test_wired_into_both_phone_doctors(self):
        source=(ROOT/"src/main.py").read_text()
        ast.parse(source)
        self.assertIn('"calculation_to_vote_trace":vote_trace',source)
        self.assertIn('"calculation_to_vote_trace":master_vote_trace',source)
        self.assertIn("from v3_vote_trace_doctor import audit_vote_trace",source)

if __name__=="__main__":unittest.main()


class R2FullDisplayProvenanceTests(unittest.TestCase):
    def test_partial_display_cannot_certify_full_published_direction(self):
        rows=boxes()
        names=("technical","candle","news","futures","options")
        evidence=[]
        for i,name in enumerate(names):
            active=i<4
            evidence.append(EngineEvidence(name,80 if active else None,
                                           20 if active else None,verified=active,
                                           timestamp=1795000000 if active else None,
                                           source="Dhan" if active else ""))
            if i<3:
                rows[i].update(status="BULLISH",raw_verified=True,raw_source="Dhan",
                               bullish_percent=80,bearish_percent=20)
        snap=compose_snapshot(**dict(zip(names,evidence)))
        self.assertEqual(snap["combined"]["coverage"],4)
        self.assertEqual(snap["combined"]["state"],"BULLISH")
        result=base(market_open=True,box_rows=rows,snapshot=snap)
        self.assertEqual(result["box_vote_gate"]["eligible"],3)
        self.assertEqual(result["combined_vote"]["state"],"WAIT")
        self.assertEqual(result["combined_vote"]["reason"],"DISPLAY_SIDE_PROVENANCE_NOT_VERIFIED")
        rows[3].update(status="BULLISH",raw_verified=True,raw_source="Dhan",
                       bullish_percent=80,bearish_percent=20)
        self.assertEqual(base(market_open=True,box_rows=rows,snapshot=snap)
                         ["combined_vote"]["state"],"BULLISH")
