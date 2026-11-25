import unittest
from v3_smart_active_doctor import active_report

class SmartActiveDoctorTests(unittest.TestCase):
    def test_healthy_hidden_and_regressions_reappear(self):
        args=dict(generation=1,symbols=["TCS","INFY"],quote_present=["TCS","INFY"],
                  index_present=["NIFTY","BANKNIFTY","SENSEX"],
                  connected={"Dhan":True,"Oracle":True},signal_present=["TCS","INFY"],
                  attempts={"TCS":10,"INFY":20},now_monotonic=50,market_open=True,
                  errors=[],progress={},performance={},quote_attempt_age=5)
        report=active_report(**args)
        self.assertEqual(report["healthy_hidden_count"],6)
        self.assertFalse(report["source_live_verified"])
        self.assertEqual(report["provider_requests"],0)
        self.assertEqual(report["orders_sent"],0)
        self.assertEqual(report["active"][0]["oldest_attempt_symbols"],["TCS","INFY"])
        args["quote_present"]=["TCS"]
        args["errors"]=["index"]
        report=active_report(**args)
        self.assertEqual(report["healthy_hidden_count"],4)
        self.assertIn("EQUITY_QUOTE_COVERAGE",[r["check"] for r in report["active"]])
        self.assertIn("OBSERVED_ERRORS",[r["check"] for r in report["active"]])
        self.assertIn("FULL_FUNCTIONAL_WIRING",[r["check"] for r in report["active"]])

    def test_freshness_separates_attempt_success_and_completed_candle(self):
        report=active_report(generation=1,symbols=["A","B","C"],
            quote_present=["A","B"],index_present=[],connected={"Dhan":True},
            signal_present=["A","B"],attempts={"A":99},now_monotonic=100,
            market_open=True,errors=[],progress={},performance={},
            quote_attempt_age=1,quote_success_age=40,
            candle_stamps={"A":500,"B":900,"C":1100},now_epoch=1000)
        row=next(r for r in report["active"] if r["check"]=="CONTINUOUS_QUOTE_AND_CANDLE_FRESHNESS")
        self.assertEqual(row["last_quote_success_age_seconds"],40)
        self.assertEqual(row["completed_3m_timestamp_count"],2)
        self.assertEqual(row["older_than_360s_count"],1)
        self.assertEqual(row["missing_completed_3m_timestamp_count"],1)
        self.assertEqual(row["oldest_candles"][0]["symbol"],"A")
        self.assertFalse(row["exchange_live_verified"])

    def test_final_vote_frame_observation_is_scoped_and_generation_safe(self):
        from v3_smart_active_doctor import final_vote_frame_observation
        args=dict(generation=1,symbols=["TCS"],quote_present=["TCS"],
                  index_present=["NIFTY","BANKNIFTY","SENSEX"],
                  connected={"Dhan":True},signal_present=["TCS"],attempts={},
                  now_monotonic=50,market_open=False,errors=[],progress={},
                  performance={},quote_attempt_age=None)
        for frame in ("1m","3m","5m","15m"):
            obs=final_vote_frame_observation(symbol="TCS",timeframe=frame,
                      generation=1,display_mode="HISTORICAL")
            report=active_report(**args,final_vote_observation=obs)
            rows=[r for r in report["active"] if r["check"]=="FINAL_VOTE_FRAME_GUARD"]
            self.assertEqual(obs["provider_requests"],0)
            self.assertIn("parity not measured",obs["scope"])
            if frame=="15m":
                self.assertEqual(rows[0]["code"],"BK-FINAL-FRAME-001")
                self.assertEqual(rows[0]["status"],"UNVERIFIED")
            else:
                self.assertEqual(rows,[])
        obs["generation"]=0
        report=active_report(**args,final_vote_observation=obs)
        row=next(r for r in report["active"] if r["check"]=="FINAL_VOTE_FRAME_GUARD")
        self.assertEqual(row["code"],"BK-FINAL-FRAME-002")

    def test_quote_contract_lane_generation_recovery_and_redaction(self):
        from clone_v2_gateway import FeedError
        from v3_smart_active_doctor import QuoteContractObservation
        tracker=QuoteContractObservation()
        exc=FeedError("BK-QUOTE-001: private-value")
        tracker.failed("indices",1,2,exc)
        tracker.failed("equities",2,2,ValueError("BK-QUOTE-001: fake"))
        self.assertEqual(tracker.active(2),[])
        for lane in ("indices","equities"):
            tracker.failed(lane,2,2,exc)
        self.assertEqual(len(tracker.active(2)),2)
        self.assertNotIn("private-value",str(tracker.active(2)))
        self.assertEqual(tracker.active(3),[])
        tracker.recovered("indices",2,3)
        self.assertEqual(len(tracker.active(2)),2)
        tracker.recovered("indices",2,2)
        args=dict(generation=2,symbols=["TCS"],quote_present=["TCS"],
                  index_present=[],connected={"Dhan":True},signal_present=[],
                  attempts={},now_monotonic=50,market_open=False,
                  errors=[],progress={},performance={},quote_attempt_age=None)
        report=active_report(**args,quote_contract_errors=tracker.active(2))
        rows=[r for r in report["active"] if r["check"]=="QUOTE_CONTRACT"]
        self.assertEqual([r["lane"] for r in rows],["equities"])
        self.assertFalse(report["source_live_verified"])
        tracker.recovered("equities",2,2)
        self.assertEqual(tracker.active(2),[])

    def test_quote_contract_both_doctors_and_workers_wired(self):
        from pathlib import Path
        source=(Path(__file__).resolve().parents[1]/"src/main.py").read_text()
        for lane in ("indices","equities"):
            self.assertIn('quote_contract_observation.failed("'+lane+'",generation,provider_generation[0],exc)',source)
            self.assertIn('quote_contract_observation.recovered("'+lane+'",generation,provider_generation[0])',source)
        self.assertIn('"quote_contract_errors":quote_contract_observation.active(generation)',source)
        self.assertIn('quote_contract_errors=quote_contract_observation.active(generation)',source)
