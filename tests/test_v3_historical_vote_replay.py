"""Actual historical evidence replay remains separate from synthetic policy tests."""
import unittest,sys,pathlib,ast
from datetime import datetime,timezone,timedelta
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from v3_historical_vote_replay import historical_vote_replay,simulated_conflict_policy_matrix
IST=timezone(timedelta(hours=5,minutes=30))
def bars():
    start=int(datetime(2026,11,23,9,15,tzinfo=IST).timestamp())
    arr=[]
    for i in range(375):
        p=25350+(i%5)
        arr.append([start+i*60,p,p+2,p-2,p+1 if i%2 else p-1,916+i])
    return arr

def replay(**kwargs):
    params=dict(symbol="NIFTY",timeframe="1m",generation=1,
                source="Dhan",bars=bars(),filter_rows=[
                    {"name":"MACD","vote":1},{"name":"VWAP","vote":-1},
                    {"name":"Pivot Points","vote":-1},
                    {"name":"OI Support","vote":None}])
    params.update(kwargs)
    return historical_vote_replay(**params)

class HistoricalVotingTests(unittest.TestCase):
    def test_real_historical_technical_and_candle_vote_not_live(self):
        r=replay()
        self.assertEqual(r["technical_vote"]["bullish"],33)
        self.assertEqual(r["technical_vote"]["bearish"],67)
        self.assertTrue(r["technical_vote"]["historical"])
        self.assertEqual(r["boxes"][0]["state"],"HIST_VOTE")
        self.assertEqual(r["boxes"][1]["state"],"HIST_VOTE")
        self.assertEqual(r["boxes"][2]["state"],"WAIT")
        self.assertEqual(r["combined"]["state"],"WAIT")
        self.assertEqual(r["combined"]["coverage"],2)
        self.assertFalse(r["verified_live"])
        self.assertEqual(r["provider_requests"],0)
    def test_independent_historical_four_box_evidence_contract(self):
        session=bars()
        stamp=session[-1][0]
        def evidence(name, basis, **extra):
            return dict(source="Dhan",verified=True,historical=True,
                        symbol="NIFTY",timeframe="1m",generation=1,
                        timestamp=stamp,bullish=75,bearish=25,
                        direction_basis=basis,**extra)
        hist=dict(
            news=evidence("news","verified_symbol_news_impact"),
            futures=evidence("futures","validated_futures_trade_flow",
                             contract="NIFTY-FUT-202611"),
            options=evidence("options","validated_option_trade_flow",
                             contract="NIFTY-25350-CE",expiry="2026-11-23",
                             underlying="NIFTY"))
        result=replay(historical_context=hist)
        self.assertEqual([v["state"] for v in result["boxes"]],
                         ["HIST_VOTE","HIST_VOTE","HIST_VOTE","HIST_VOTE","HIST_VOTE"])
        self.assertTrue(all(v["eligible_live"] is False for v in result["boxes"]))
        self.assertFalse(result["verified_live"])
        self.assertEqual(result["combined"]["state"],"WAIT")
        self.assertEqual(result["combined"]["coverage"],5)
        self.assertEqual(result["orders_sent"],0)

    def test_unverified_context_never_claims_four_box_votes(self):
        # Data-only context and mismatched proof never vote.
        bad=dict(news={"headlines":20,"direction":"BULLISH"},
                 futures={"source":"Dhan","price":25300},
                 options={"source":"Dhan","pcr":1.5,"max_pain":25350})
        result=replay(historical_context=bad)
        self.assertEqual([v["state"] for v in result["boxes"]][2:],
                         ["WAIT","WAIT","WAIT"])
        self.assertEqual(result["boxes"][2]["reason"],
                         "VERIFIED_HISTORICAL_NEWS_IMPACT_MISSING")
        self.assertEqual(result["boxes"][3]["reason"],
                         "VERIFIED_HISTORICAL_FUTURES_FLOW_MISSING")
        self.assertEqual(result["boxes"][4]["reason"],
                         "VERIFIED_EXPIRY_SCOPED_OPTION_FLOW_MISSING")
        valid=dict(source="Dhan",verified=True,historical=True,
                   symbol="NIFTY",timeframe="1m",generation=1,
                   timestamp=bars()[-1][0],bullish=70,bearish=30,
                   direction_basis="validated_option_trade_flow",
                   contract="NIFTY-CE",expiry="2026-11-23",
                   underlying="NIFTY")
        for change in ({"generation":2},{"symbol":"BANKNIFTY"},
                       {"timestamp":bars()[-1][0]+100},
                       {"verified":False},{"expiry":""},
                       {"underlying":"RELIANCE"},{"direction_basis":"pcr"},
                       {"bearish":40}):
            row=dict(valid,**change)
            self.assertEqual(replay(historical_context={"options":row})
                             ["boxes"][4]["state"],"WAIT")

    def test_candle_doji_wait_has_distinct_reason(self):
        rows=bars()
        for b in rows[-8:]:
            b[4]=b[1]
        result=replay(bars=rows)
        self.assertEqual(result["boxes"][1]["state"],"WAIT")
        self.assertEqual(result["boxes"][1]["reason"],
                         "INSUFFICIENT_VALID_COMPLETED_DIRECTIONAL_CANDLES")
    def test_non_session_tail_excluded_without_mutating(self):
        arr=bars()
        arr.append([int(datetime(2026,11,23,19,57,tzinfo=IST).timestamp()),
                    25349.65,25349.65,25349.65,25349.65,0])
        before=[v[:] for v in arr]
        r=replay(bars=arr)
        self.assertEqual(r["removed_outside_session_bars"],1)
        self.assertEqual(arr,before)
    def test_missing_data_never_invents_five_live_votes(self):
        r=replay(source="Yahoo")
        self.assertEqual(r["boxes"],[])
        self.assertEqual(r["combined"]["state"],"WAIT")
    def test_synthetic_policy_is_very_explicitly_not_live(self):
        s=simulated_conflict_policy_matrix()
        self.assertEqual(s["results"]["FOUR_BULL_ONE_BEAR"],"BULLISH")
        self.assertEqual(s["results"]["THREE_BULL_TWO_BEAR"],"WAIT")
        self.assertEqual(s["results"]["FOUR_BEAR_ONE_BULL"],"BEARISH")
        self.assertFalse(s["live_verified"])
    def test_b178_and_master_doctors_integrate_same_historical_replay(self):
        s=(ROOT/"src/main.py").read_text()
        ast.parse(s)
        self.assertIn('source=history.get("source"),bars=bars,',s)
        self.assertNotIn('source=history.get("source"),bars=completed_bars,',s)
        self.assertIn('"historical_vote_replay":historical_replay',s)
        self.assertIn('"historical_vote_replay":master_historical_replay',s)
        self.assertIn('"voting_policy_self_test":simulated_conflict_policy_matrix()',s)
if __name__=="__main__":unittest.main()
