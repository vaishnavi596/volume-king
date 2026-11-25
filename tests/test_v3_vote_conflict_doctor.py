"""Vote Conflict Doctor: disagreement is not a runtime error, no fake live."""
import unittest
import pathlib
import sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from five_engine import ENGINE_NAMES,EngineEvidence,compose_snapshot
from v3_vote_conflict_doctor import conflict_doctor
from v3_vote_trace_doctor import audit_vote_trace

def snap(directions):
    rows={}
    for name,direction in zip(ENGINE_NAMES,directions):
        bull,bear=({"B":(80,20),"S":(20,80),"N":(50,50)}[direction]
                   if direction is not None else (None,None))
        rows[name]=EngineEvidence(name,bull,bear,verified=direction is not None,
                                  timestamp=1795000000 if direction is not None else None,
                                  source="Dhan" if direction is not None else "")
    return compose_snapshot(**rows)

class ConflictDoctorTests(unittest.TestCase):
    def test_four_bull_one_bear_is_valid_minority_not_error(self):
        result=conflict_doctor(snap("BBBBS"),market_open=True)
        self.assertEqual(result["status"],"MINORITY_VOTE_RETAINED")
        self.assertEqual(result["final_state"],"BULLISH")
        self.assertEqual(result["bullish_boxes"],4)
        self.assertEqual(result["bearish_boxes"],1)
        self.assertEqual(result["issues"],[])
    def test_three_vs_two_is_wait_not_error(self):
        result=conflict_doctor(snap("BBBSS"),market_open=True)
        self.assertEqual(result["status"],"CONFLICT_NO_CONSENSUS")
        self.assertEqual(result["final_state"],"WAIT")
        self.assertEqual(result["issues"],[])
    def test_four_bear_one_bull(self):
        result=conflict_doctor(snap("SSSSB"),market_open=True)
        self.assertEqual(result["final_state"],"BEARISH")
        self.assertTrue(result["normal_disagreement"])
    def test_unverified_engine_is_not_a_vote(self):
        result=conflict_doctor(snap(["B","S",None,None,None]),market_open=True)
        self.assertEqual(result["eligible_boxes"],2)
        self.assertEqual(result["final_state"],"WAIT")
        self.assertEqual(result["status"],"WAIT_INSUFFICIENT_VERIFIED_ENGINES")
    def test_publish_mismatch_is_real_error(self):
        data=snap("BBBBS")
        data["combined"]=dict(data["combined"],state="BEARISH")
        result=conflict_doctor(data,market_open=True)
        self.assertEqual(result["issues"][0]["code"],"COMBINED_VOTE_PUBLISH_MISMATCH")
    def test_market_close_never_claims_live(self):
        result=conflict_doctor(snap("BBBBS"),market_open=False)
        self.assertEqual(result["final_state"],"WAIT")
        self.assertEqual(result["issues"],[])
    def test_trace_wiring_and_sixth_standby(self):
        r=audit_vote_trace(symbol="NIFTY",timeframe="1m",generation=1,
            filter_rows=[{"name":"EMA 9/21","vote":1,"status":"BULLISH"}],
            box_rows=[{"engine":n,"status":"WAIT","raw_verified":False,
                       "blocker":"UNVERIFIED"} for n in ENGINE_NAMES],
            snapshot=snap("BBBSS"),market_open=True)
        self.assertEqual(r["voting_conflict_audit"]["status"],"CONFLICT_NO_CONSENSUS")
        self.assertEqual(r["voting_conflict_audit"]["issues"],[])
        self.assertEqual(r["box_vote_gate"]["sixth_M"],"STANDBY_NOT_SCORED")
        self.assertEqual(r["provider_requests"],0)
if __name__=="__main__":unittest.main()


class R2ConflictPublicationTests(unittest.TestCase):
    def test_conflicting_or_missing_aggregate_cannot_certify_final_direction(self):
        original=snap("BBBBS")
        self.assertEqual(conflict_doctor(original,market_open=True)["final_state"],"BULLISH")
        broken=dict(original,combined=dict(original["combined"],state="BEARISH"))
        self.assertEqual(conflict_doctor(broken,market_open=True)["final_state"],"WAIT")
        self.assertEqual(conflict_doctor(broken,market_open=True)["status"],
                         "COMBINED_VOTE_PUBLISH_MISMATCH")
        self.assertEqual(conflict_doctor({"engines":original["engines"]},market_open=True)
                         ["final_state"],"WAIT")
