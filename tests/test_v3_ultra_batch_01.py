import unittest
from datetime import date
from backend.option_evidence_cache import OptionEvidenceCache
from backend.futures_context import normalize_futures_ltp,select_verified_future
from v3_stock_diagnostics import classify_stock,DiagnosticRegistry
from v3_market_display_mode import restored_quote_rows
from dhan_multi_timeframe import completed_derived_bars
from v3_hist_close_display import historical_close_display
from five_engine import measured_directional_evidence

class UltraBatchTests(unittest.TestCase):
    def test_option_cache_rejects_foreign_and_invalid_clock(self):
        clock=[10]
        c=OptionEvidenceCache(clock=lambda:clock[0],today=lambda:date(2026,11,26))
        m=dict(source="dhan",signal_eligible=False,freshness="unverified")
        self.assertFalse(c.put("NIFTY","2026-12-31",dict(m,symbol="TCS")))
        self.assertFalse(c.put("NIFTY","2026-12-31",dict(m,expiry="2027-01-01")))
        self.assertFalse(c.put("NIFTY","2026-12-31",dict(m,live_verified=True)))
        self.assertTrue(c.put("NIFTY","2026-12-31",m))
        clock[0]=float("nan")
        self.assertIsNone(c.latest("NIFTY"))
        self.assertFalse(c.put("NIFTY","2026-12-31",m))
        with self.assertRaises(ValueError):OptionEvidenceCache(max_entries=True)

    def test_futures_mapping_invalid(self):
        self.assertIsNone(normalize_futures_ltp({"status":"success","data":{}},None))
        expiry=date(2026,12,31)
        row=dict(source="Dhan",master_verified=True,instrument_type="FUT",exchange_segment="NSE_FNO",underlying="NIFTY",expiry=expiry.isoformat(),security_id="9"*5000,contract="NIFTY FUT")
        self.assertIsNone(select_verified_future([row],"NIFTY",expiry))

    def test_foreign_cache_and_stale_doctor_generation(self):
        bars=[[100,100,102,99,101,1],[160,100,102,99,101,1]]
        h={("NIFTY","1m",2):dict(source="Dhan",symbol="TCS",bars=bars)}
        out=classify_stock("NIFTY",dict(source="Dhan",symbol="TCS",price=100),h,2,required_frames=("1m",))
        self.assertIn("SYMBOL_MISMATCH",out["error_codes"])
        reg=DiagnosticRegistry()
        reg.reconcile([out],2)
        self.assertEqual(reg.reconcile([],1)["active_count"],1)
        self.assertEqual(restored_quote_rows(None,source="Dhan"),{})

    def test_candle_overflow_is_not_a_crash(self):
        self.assertEqual(completed_derived_bars([[1e100,100,102,99,101,1]],"5m",now_epoch=1e101),[])
        self.assertIsNone(historical_close_display(dict(source="Dhan",_scanner_timeframe="3m",bars=[[1e100,100,102,99,101,1]]),now=1e101))

    def test_conflicting_live_flag_cannot_vote(self):
        row=dict(source="Dhan",verified=True,direction_basis="validated_trade_flow",contract="NIFTY FUT",bullish=80,bearish=20,timestamp=100,verified_live=False)
        self.assertFalse(measured_directional_evidence("futures",row,required_basis="validated_trade_flow").eligible)
