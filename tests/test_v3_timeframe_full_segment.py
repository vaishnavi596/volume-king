"""One gated V3 1m/3m/5m/10m/15m/30m candle segment.

Offline only. Derived frames never borrow wrong source/timeframe or
display unfinished/duplicated/overnight candles as complete.
"""
import ast
from datetime import datetime,timezone,timedelta
from pathlib import Path
import unittest
from dhan_multi_timeframe import completed_derived_bars
from dhan_three_minute import completed_three_minute_bars
from v3_live_capacity_probe import benchmark_cached_capacity

IST=timezone(timedelta(hours=5,minutes=30))
DAY=datetime(2026,11,20,9,15,tzinfo=IST).timestamp()

def series(minutes,n=50):
    return [[DAY+i*minutes*60,100+i*.1,101+i*.1,99+i*.1,100.5+i*.1,1000+i]
            for i in range(n)]
class TestSixFrameGate(unittest.TestCase):
    def test_10m_from_5m_ohlcv(self):
        s=series(5,6)
        bars=completed_derived_bars(s,"10m",now_epoch=DAY+3600)
        self.assertEqual(len(bars),3)
        self.assertEqual(bars[0][0],DAY)
        self.assertEqual(bars[0][1],s[0][1])
        self.assertEqual(bars[0][2],max(s[0][2],s[1][2]))
        self.assertEqual(bars[0][3],min(s[0][3],s[1][3]))
        self.assertEqual(bars[0][4],s[1][4])
        self.assertEqual(bars[0][5],s[0][5]+s[1][5])
    def test_30m_from_15m(self):
        s=series(15,8)
        bars=completed_derived_bars(s,"30m",now_epoch=DAY+3600*3)
        self.assertEqual(len(bars),4)
        self.assertEqual(bars[0][0],DAY)
    def test_partial_10m_group_not_published(self):
        s=series(5,5)
        bars=completed_derived_bars(s,"10m",now_epoch=DAY+24*3600)
        self.assertEqual(len(bars),2)
        self.assertEqual(len(completed_derived_bars(series(5,2),"10m",now_epoch=DAY+9*60)),0)
    def test_duplicate_and_missing_source_rejected(self):
        s=series(5,4)
        self.assertEqual(len(completed_derived_bars([s[0],s[0],s[1]],"10m",now_epoch=DAY+3600)),0)
        self.assertEqual(len(completed_derived_bars([s[0],s[2]],"10m",now_epoch=DAY+3600)),0)
        with self.assertRaises(ValueError):
            completed_derived_bars(s,"3m",now_epoch=DAY+3600)
    def test_no_cross_session_or_market_close_partial(self):
        s=series(15,25)
        bars=completed_derived_bars(s,"30m",now_epoch=DAY+24*3600)
        self.assertEqual(len(bars),12) # 375min session ends with odd 15m
        self.assertLessEqual(bars[-1][0]+1800,DAY+375*60)
    def test_real_cache_doctor_all_six(self):
        histories={
            ("NIFTY","1m",9):{"source":"Dhan","_scanner_timeframe":"1m","bars":series(1,90)},
            ("NIFTY","5m",9):{"source":"Dhan","_scanner_timeframe":"5m","bars":series(5,18)},
            ("NIFTY","15m",9):{"source":"Dhan","_scanner_timeframe":"15m","bars":series(15,6)}}
        out=benchmark_cached_capacity([],{"NIFTY":{"source":"Dhan","price":100}},histories,9,51)
        self.assertEqual(list(out["history_presence"]),["1m","3m","5m","10m","15m","30m"])
        self.assertEqual({k:out["history_presence"][k] for k in ("1m","3m","5m","10m","15m","30m")},
                         {k:1 for k in ("1m","3m","5m","10m","15m","30m")})
        self.assertEqual(out["derived_10m_30m_from_complete_source"],{"10m":1,"30m":1})
        self.assertEqual(out["derived_3m_from_valid_1m"],1)
    def test_main_source_wires_both_screens_and_provider(self):
        main=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text()
        tree=ast.parse(main)
        funcs={n.name:ast.get_source_segment(main,n) or "" for n in ast.walk(tree)
               if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        self.assertIn('"10m","15m","30m"',funcs["fetch_market_data_uncached"])
        self.assertIn('completed_derived_bars(candle_result["bars"],interval',funcs["fetch_market_data_uncached"])
        self.assertIn('completed_derived_bars(source["bars"],tf',funcs["shared_history"])
        self.assertIn('"10m","15m","30m"',main)
        self.assertIn('"10m":(600,37.5',funcs["timeframe_spec"])
        self.assertIn('"30m":(1800,12.5',funcs["timeframe_spec"])

if __name__=="__main__":
    unittest.main()
