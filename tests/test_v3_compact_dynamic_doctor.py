"""V3 one active-only <=70 equity Doctor test, resolved rows remain hidden."""
import ast
import pathlib
import sys
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from v3_compact_doctor import compact_doctor
from v3_live_capacity_probe import benchmark_cached_capacity
MAIN=(ROOT/"src/main.py").read_text(encoding="utf-8")
class CompactDynamicDoctorTests(unittest.TestCase):
    def test_one_active_test_only_and_70_is_capacity_not_workload(self):
        ast.parse(MAIN)
        panel=MAIN.split("    def v3_live_building_panel():",1)[1].split("    def settings():",1)[0]
        self.assertIn('async def run_cached_test(e):',panel)
        self.assertIn('count=len(chosen)',panel)
        self.assertIn('[:70]',panel)
        self.assertIn('TEST ACTIVE • MAX 70 EQUITIES (+3 INDICES)',panel)
        self.assertNotIn('ft.OutlinedButton("TEST 54',panel)
        self.assertNotIn('ft.OutlinedButton("TEST 70 SHARES',panel)
        one=benchmark_cached_capacity(["RELIANCE","RELIANCE"],{}, {},1,1)
        self.assertEqual(one["observed_instruments"],4)
        self.assertEqual(one["unselected_equity_slots"],0)
    def test_errors_only_does_not_repeat_thirteen_healthy_results(self):
        chosen=["EMA 9/21","RSI 14","OI Support","Dhan Max Pain"]
        rows=[{"name":"EMA 9/21","vote":1},{"name":"RSI 14","vote":0},
              {"name":"OI Support","vote":None},{"name":"Dhan Max Pain","vote":None}]
        result=compact_doctor([],chosen,rows,scanner_symbol="NIFTY",
                              scanner_timeframe="1m",provider_connected=True)
        self.assertEqual(result["selected_filter_count"],4)
        self.assertEqual(result["healthy_filter_count_hidden"],2)
        self.assertEqual(result["issue_count"],2)
        self.assertEqual({v["name"] for v in result["filter_results"]},
                         {"OI Support","Dhan Max Pain"})
        self.assertEqual(result["orders_sent"],0)
if __name__=="__main__":unittest.main()
