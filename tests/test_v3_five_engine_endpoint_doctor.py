"""The endpoint Doctor must distinguish HIST from five verified LIVE sources."""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"src"))
from five_engine_endpoint_doctor import five_engine_endpoint_diagnostic

class EndpointDoctorTests(unittest.TestCase):
    def kwargs(self):
        return dict(symbol="NIFTY",timeframe="1m",generation=1,
                    technical_calculated=13,technical_total=13,
                    historical_technical_votes=3,historical_candle_directional=0,
                    news_headline_count=20,option_context_present=True,
                    snapshots_present=False,market_open=False,
                    exchange_timestamp_verified=False)
    def test_closed_session_keeps_historical_and_reports_five_endpoints(self):
        r=five_engine_endpoint_diagnostic(**self.kwargs())
        self.assertEqual(len(r["box_paths"]),5)
        self.assertEqual(r["box_paths"][0]["historical_state"],"HIST_CALCULATED")
        self.assertEqual(r["box_paths"][0]["blocked_at"],"EXACT_FRAME_PUBLISH_MISSING")
        self.assertEqual(r["box_paths"][1]["historical_state"],"HIST_WAIT_INSUFFICIENT_DIRECTIONAL_BODIES")
        self.assertEqual(r["box_paths"][2]["historical_state"],"HEADLINE_CONTEXT_ONLY")
        self.assertEqual(r["box_paths"][4]["historical_state"],"OPTION_CHAIN_CONTEXT_ONLY")
        self.assertTrue(all(x["live_state"]=="MARKET_CLOSED" and not x["verified_live"] for x in r["box_paths"]))
        self.assertEqual(r["orders_sent"],0)
    def test_publisher_available_does_not_turn_unverified_source_live(self):
        k=self.kwargs();k.update(snapshots_present=True,market_open=True)
        r=five_engine_endpoint_diagnostic(**k)
        self.assertEqual(r["box_paths"][0]["blocked_at"],"SOURCE_EXCHANGE_TIMESTAMP_UNVERIFIED")
        self.assertTrue(all(x["live_state"]=="NOT_VERIFIED" for x in r["box_paths"]))
        self.assertEqual(r["live_verified_box_count"],0)
    def test_required_exact_identity(self):
        k=self.kwargs();k["timeframe"]="2m"
        with self.assertRaises(ValueError):five_engine_endpoint_diagnostic(**k)

if __name__=="__main__": unittest.main()
