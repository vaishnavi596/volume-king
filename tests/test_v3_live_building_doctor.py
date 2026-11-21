"""Offline V3 first-cache/readiness and adaptive UI timing tests."""
import unittest
from v3_building_doctor import BuildingDoctor,FRAMES,INDICES

class TestBuildingDoctor(unittest.TestCase):
    def test_login_milestones_are_monotonic_and_no_secrets(self):
        d=BuildingDoctor()
        d.start_login()
        d.milestone("gateway_authorized")
        d.milestone("quotes_response_received")
        d.milestone("quotes_applied_to_phone_stock")
        milestones=d.report([],{}, {},0)["login_milestones_seconds"]
        self.assertLessEqual(milestones["gateway_authorized"],milestones["quotes_response_received"])
        self.assertLessEqual(milestones["quotes_response_received"],milestones["quotes_applied_to_phone_stock"])
        self.assertNotIn("token",str(milestones).lower())

    def test_partial_never_called_live(self):
        d=BuildingDoctor()
        got=d.report(["EQ01"],{}, {},1,connected=False)
        self.assertEqual(got["state"],"PARTIAL_WAIT")
        self.assertFalse(got["source_quality_verified_live"])
        self.assertEqual(got["instruments"],4)

    def test_complete_presence_not_live(self):
        d=BuildingDoctor()
        names=(*INDICES,"EQ01")
        q={s:{"source":"Dhan","price":101} for s in names}
        h={(s,tf,2):{"source":"Dhan","_scanner_timeframe":tf,"bars":[[1,1,2,.9,1.4,3],[2,1,2,.9,1.4,3]]}
            for s in names for tf in FRAMES}
        got=d.report(["EQ01"],q,h,2,connected=True)
        self.assertTrue(got["cache_complete_presence"])
        self.assertEqual(got["state"],"FULL_STOCK_OBSERVED_UNVERIFIED")
        self.assertFalse(got["source_quality_verified_live"])
        self.assertEqual(got["candle_presence_by_frame"],{"1m":4,"3m":4,"5m":4})
        self.assertFalse(d.report(["EQ01"],q,h,3)["cache_complete_presence"])

    def test_cross_timeframe_not_promoted(self):
        d=BuildingDoctor()
        h={("NIFTY","3m",1):{"source":"Dhan","_scanner_timeframe":"1m","bars":[1,2]}}
        self.assertEqual(d.report([],{},h,1)["candle_presence_by_frame"]["3m"],0)

    def test_adaptive_bounds_no_fixed_1_or_3_minute(self):
        d=BuildingDoctor()
        self.assertEqual(d.adaptive_gap("dashboard"),.25)
        for t in [1,20,60,600,4000]:d.observe("mounted_refresh_ms",t)
        self.assertTrue(.10<=d.adaptive_gap("dashboard")<=1.5)
        self.assertTrue(.10<=d.adaptive_gap("scanner")<=1.5)
        d.observe("mounted_refresh_ms",-10)
        self.assertEqual(len(d.samples["mounted_refresh_ms"]),5)

    def test_no_arbitrary_30s_or_60s_data_deadline(self):
        d=BuildingDoctor()
        d.started-=180
        got=d.report([],{}, {},0)
        self.assertEqual(got["state"],"PARTIAL_WAIT")
        self.assertGreaterEqual(got["elapsed_session_s"],180)

if __name__=="__main__":unittest.main()
