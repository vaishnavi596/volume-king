"""B1 actual-stock typed diagnostics and bounded recovery without network requests."""
import unittest
from datetime import datetime,timezone,timedelta
from v3_stock_diagnostics import classify_stock,DiagnosticRegistry
from v3_live_capacity_probe import benchmark_cached_capacity

def bars():
    start=datetime(2026,11,20,9,15,tzinfo=timezone(timedelta(hours=5,minutes=30))).timestamp()
    return [[start+60*i,101,102,100,101.5,500] for i in range(40)]

def records(symbol="NIFTY",generation=1):
    return {(symbol,frame,generation):{"source":"Dhan","_scanner_timeframe":frame,"bars":bars()}
            for frame in ("1m","3m","5m","10m","15m","30m")}

class TestTypedStockDoctor(unittest.TestCase):
    def test_missing_data_is_typed_error_never_direction(self):
        entry=classify_stock("NIFTY",{}, {},1)
        self.assertEqual(entry["state"],"ERROR")
        self.assertEqual(entry["error_codes"],["DATA_INCOMPLETE"])
        self.assertFalse(entry["analysis_eligible"])
        self.assertFalse(entry["live_signal_eligible"])
    def test_wrong_timeframe_and_invalid_candle(self):
        h=records()
        h[("NIFTY","3m",1)]["_scanner_timeframe"]="1m"
        h[("NIFTY","5m",1)]["bars"]=[[1,10,9,11,10,1],[2,10,11,9,10,1]]
        result=classify_stock("NIFTY",{"source":"Dhan","price":100},h,1,
                                required_frames=("1m","3m","5m","10m","15m","30m"))
        self.assertIn("TIMEFRAME_MISMATCH",result["error_codes"])
        self.assertIn("CANDLE_INVALID",result["error_codes"])
        self.assertEqual(result["state"],"ERROR")
    def test_recovery_and_missing_peer_still_processed(self):
        registry=DiagnosticRegistry()
        bad=classify_stock("NIFTY",{}, {},1)
        good=classify_stock("BANKNIFTY",{"source":"Dhan","price":100},records("BANKNIFTY"),1)
        self.assertEqual(registry.reconcile([bad,good],1)["active_count"],1)
        healthy_nifty=classify_stock("NIFTY",{"source":"Dhan","price":100},records(),1)
        result=registry.reconcile([healthy_nifty,good],1)
        self.assertEqual(result["active_count"],0)
        self.assertTrue(any(x["state"]=="RESOLVED" and x["symbol"]=="NIFTY" for x in result["recent_events"]))
    def test_other_share_absent_from_followup_is_not_resolved(self):
        registry=DiagnosticRegistry()
        registry.reconcile([classify_stock("NIFTY",{}, {},1)],1)
        self.assertEqual(registry.reconcile([],1)["active_count"],1)
        self.assertEqual(registry.reconcile([],2)["active_count"],0)
    def test_actual_cache_report_shows_independent_errors(self):
        q={"NIFTY":{"source":"Dhan","price":100}}
        h=records()
        out=benchmark_cached_capacity(["RELIANCE"],q,h,1,70)
        self.assertEqual(out["requested_instruments"],73)
        self.assertEqual(out["stock_error_count"],3)
        self.assertEqual(out["unconfigured_symbols_are_not_provider_errors"],69)
        self.assertTrue(any(s["symbol"]=="RELIANCE" and s["state"]=="ERROR" for s in out["stock_states"]))
        self.assertFalse(any(s["live_signal_eligible"] for s in out["stock_states"]))

if __name__=="__main__":
    unittest.main()
