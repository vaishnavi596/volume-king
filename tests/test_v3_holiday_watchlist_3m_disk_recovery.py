"""Executable shared_history regression: phone restart 1m disk -> completed 3m HIST.

No provider connection, HTTP calls, LIVE promotion or broker orders.
"""
import ast
import math
import pathlib
import sys
import time
import types
import unittest
from datetime import datetime,timedelta,timezone

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from candle_retention import valid_candle_history

IST=timezone(timedelta(hours=5,minutes=30))
SOURCE=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
NODES=[node for node in ast.walk(ast.parse(SOURCE))
       if isinstance(node,ast.FunctionDef) and node.name=="shared_history"]

def fake_hist():
    stamp=int(datetime(2026,11,23,9,15,tzinfo=IST).timestamp())
    return {"source":"Dhan","_scanner_timeframe":"1m",
            "live_verified":False,"freshness":"historical_unverified",
            "bars":[[stamp+i*60,25000+i/5,25002+i/5,24998+i/5,
                     25001+i/5,100+i] for i in range(120)]}

class FakeStore:
    def __init__(self,record):
        self.record=record
        self.gets=[]
    def get(self,*parts):
        self.gets.append(parts)
        if parts[:4]==("market","Dhan","NIFTY","1m"):
            return self.record
        return None

def load_shared(saved):
    assert len(NODES)==1
    env={"prefs":{"source":"Dhan"},"provider_generation":[1],
         "scan_generation":[2],"chart_snapshots":{},"quotes":{},"candles":{},
         "derived_three_minute_cache":{},"market_store":FakeStore(saved),
         "valid_candle_history":valid_candle_history,"math":math,"time":time}
    exec(compile(ast.fix_missing_locations(
        ast.Module(body=[NODES[0]],type_ignores=[])),str(ROOT/"src"/"main.py"),"exec"),env)
    return env["shared_history"],env["market_store"]

class HolidayWatchlist3mFromDisk(unittest.TestCase):
    def test_last_good_disk_1m_restores_watchlist_3m_without_network(self):
        shared,store=load_shared(fake_hist())
        result=shared("NIFTY","3m")
        self.assertEqual(result.get("source"),"Dhan")
        self.assertEqual(result.get("_scanner_timeframe"),"3m")
        self.assertTrue(result.get("historical"))
        self.assertFalse(result.get("live_verified"))
        self.assertEqual(result.get("freshness"),"historical_unverified")
        self.assertGreaterEqual(len(result.get("bars",[])),30)
        self.assertTrue(all(
            result["bars"][i+1][0]-result["bars"][i][0]==180
            for i in range(len(result["bars"])-1)))
        self.assertEqual(store.gets[0][:4],("market","Dhan","NIFTY","3m"))
        self.assertTrue(any(x[:4]==("market","Dhan","NIFTY","1m")
                            for x in store.gets))

    def test_wrong_source_and_live_cache_cannot_be_relabelled(self):
        for changed in ({"source":"Yahoo Finance"},{"live_verified":True},
                        {"_scanner_timeframe":"5m"},{"bars":[]},):
            with self.subTest(changed=changed):
                row=dict(fake_hist(),**changed)
                shared,_=load_shared(row)
                self.assertEqual(shared("NIFTY","3m"),{})

    def test_unrelated_symbol_never_uses_nifty_disk_history(self):
        shared,_=load_shared(fake_hist())
        self.assertEqual(shared("BANKNIFTY","3m"),{})

if __name__=="__main__":
    unittest.main()
