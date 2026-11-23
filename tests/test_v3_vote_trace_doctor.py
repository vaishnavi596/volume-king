"""Ensure phone Doctor identifies calculation, vote and final display gaps."""
import ast
import pathlib
import sys
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from v3_vote_trace_doctor import audit_vote_trace
from five_engine import EngineEvidence,compose_snapshot
from scanner_engine import OPTION_FILTERS

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
    def test_missing_display_proof_does_not_turn_three_engine_snapshot_live(self):
        a=tuple(EngineEvidence(n,70 if i<3 else None,30 if i<3 else None,
                       verified=i<3,timestamp=1795000000 if i<3 else None,
                       source="Dhan" if i<3 else "")
                       for i,n in enumerate(("technical","candle","news","futures","options")))
        r=base(snapshot={"engines":a},market_open=True)
        self.assertEqual(r["combined_vote"]["state"],"WAIT")
        self.assertEqual(r["combined_vote"]["reason"],"DISPLAY_SIDE_PROVENANCE_NOT_VERIFIED")
    def test_duplicate_filter_and_box_rejected(self):
        with self.assertRaises(ValueError):
            base(filter_rows=[{"name":"EMA 9/21"},{"name":"EMA 9/21"}])
        with self.assertRaises(ValueError):
            base(box_rows=boxes()[:-1]+[boxes()[0]])
    def test_wired_into_both_phone_doctors(self):
        source=(ROOT/"src/main.py").read_text()
        ast.parse(source)
        self.assertIn('"calculation_to_vote_trace":vote_trace',source)
        self.assertIn('"calculation_to_vote_trace":master_vote_trace',source)
        self.assertIn("from v3_vote_trace_doctor import audit_vote_trace",source)

if __name__=="__main__":unittest.main()
