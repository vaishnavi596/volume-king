"""Read-only real-stock capacity benchmark: no fake broker data or provider access."""
import unittest
from datetime import datetime,timezone,timedelta
from v3_live_capacity_probe import benchmark_cached_capacity,INDEXES

def sample_bars():
    # Historical market session at minute spacing; in test only.
    day=datetime(2026,11,20,9,15,tzinfo=timezone(timedelta(hours=5,minutes=30))).timestamp()
    return [[day+j*60,100+j*.01,101+j*.01,99+j*.01,100.5+j*.01,1000] for j in range(40)]

class TestRealCapacity(unittest.TestCase):
    def test_unavailable_equities_are_wait_not_fabricated(self):
        res=benchmark_cached_capacity(["RELIANCE"],{}, {},1,70)
        self.assertEqual(res["requested_instruments"],73)
        self.assertEqual(res["observed_instruments"],4)
        self.assertEqual(res["unselected_equity_slots"],69)
        self.assertEqual(res["dhan_quote_present"],0)
        self.assertEqual(res["technical_scanner_analyzed"],0)
        self.assertIn("no network calls",res["source"])
    def test_54_target_is_51_plus_three_not_54_equities(self):
        symbols=["EQ%03d"%i for i in range(70)]
        result=benchmark_cached_capacity(symbols,{}, {},1,51)
        self.assertEqual(result["requested_instruments"],54)
        self.assertEqual(result["observed_instruments"],54)
        self.assertEqual(result["unselected_equity_slots"],0)
    def test_existing_real_cached_histories_are_computed(self):
        frames={"1m":sample_bars()}
        q={"NIFTY":{"source":"Dhan","price":100}}
        h={("NIFTY","1m",3):{"source":"Dhan","_scanner_timeframe":"1m","bars":frames["1m"]}}
        res=benchmark_cached_capacity([],q,h,3,51)
        self.assertEqual(res["history_presence"]["1m"],1)
        self.assertEqual(res["history_presence"]["3m"],1)
        self.assertEqual(res["derived_3m_from_valid_1m"],1)
        self.assertEqual(res["dhan_quote_present"],1)
        self.assertEqual(res["technical_chart_available"],1)
        self.assertEqual(res["technical_scanner_analyzed"],1)
        self.assertEqual(res["five_live_options_filters"][:12],"NOT MEASURED")
    def test_derived_3m_rejects_incomplete_minute_groups(self):
        bad=sample_bars()[:2] + sample_bars()[3:5]
        h={("NIFTY","1m",2):{"source":"Dhan","_scanner_timeframe":"1m","bars":bad}}
        res=benchmark_cached_capacity([],{},h,2,51)
        self.assertEqual(res["history_presence"]["3m"],0)
        self.assertEqual(res["derived_3m_from_valid_1m"],0)

    def test_cross_generation_and_frame_not_borrowed(self):
        h={("NIFTY","3m",1):{"source":"Dhan","_scanner_timeframe":"1m","bars":sample_bars()}}
        res=benchmark_cached_capacity([],{},h,1,51)
        self.assertEqual(res["history_presence"]["3m"],0)
        self.assertEqual(res["technical_scanner_analyzed"],0)
    def test_bounds(self):
        for invalid in (-1,71,True,54.5):
            with self.assertRaises(ValueError):
                benchmark_cached_capacity([],{}, {},1,invalid)
        result=benchmark_cached_capacity(["EQ01","EQ01"],{}, {},1,1)
        self.assertEqual(result["observed_instruments"],4)
        self.assertEqual(result["unselected_equity_slots"],0)

if __name__=="__main__":unittest.main()
