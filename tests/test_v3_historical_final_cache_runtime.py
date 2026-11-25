"""Execute the actual nested phone HIST cache function, with broker calls absent.

Stress cache identity across 70 equities / three frames; real replay correctness
is tested by test_v3_historical_vote_replay.py. Never contact Dhan/Oracle.
"""
import ast
import math
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]


class HistoricalFinalCacheRuntimeTests(unittest.TestCase):
    def setUp(self):
        source=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
        tree=ast.parse(source)
        nodes=[n for n in ast.walk(tree)
               if isinstance(n,ast.FunctionDef)
               and n.name=="cached_historical_final_replay"]
        self.assertEqual(len(nodes),1)
        program=ast.fix_missing_locations(ast.Module(body=[nodes[0]],type_ignores=[]))
        self.env={"math":math,"provider_generation":[1],
                  "prefs":{"source":"Dhan"},
                  "historical_final_replay_cache":{}}
        exec(compile(program,str(ROOT/"src"/"main.py"),"exec"),self.env)
        self.run=self.env["cached_historical_final_replay"]
        self.calls=[]
        module=types.ModuleType("v3_historical_vote_replay")
        def measured_replay(**kwargs):
            self.calls.append(kwargs)
            return {"historical_combined":{"state":"WAIT","coverage":0},
                    "identity":(kwargs["symbol"],kwargs["timeframe"])}
        module.historical_vote_replay=measured_replay
        self.replay_stub=patch.dict(sys.modules,{"v3_historical_vote_replay":module})
        self.replay_stub.start()

    def tearDown(self):
        self.replay_stub.stop()

    def test_70_equities_three_frames_quote_only_repaints_are_cache_hits(self):
        now=1795000000
        selected=[{"name":"MACD"},{"name":"EMA 9/21"}]
        histories={}
        for i in range(70):
            symbol=f"EQ{i:02d}"
            for frame in ("1m","3m","5m"):
                bars=[[now-600,100.0,101.0,99.0,100.5,20],
                      [now,100.5,101.0,100.0,100.8,21]]
                history={"source":"Dhan","_scanner_timeframe":frame,"bars":bars}
                histories[symbol,frame]=history
                result=self.run(symbol,frame,history,selected,now+10)
                self.assertEqual(result["identity"],(symbol,frame))
        self.assertEqual(len(self.calls),210)
        self.assertTrue(all(call["source"]=="Dhan" and call["bars"] is not None for call in self.calls))
        self.assertEqual(len(self.env["historical_final_replay_cache"]),210)
        # A quote-only refresh isn't part of historical candle revision identity.
        for (sym,frame),history in histories.items():
            self.run(sym,frame,history,selected,now+10)
        self.assertEqual(len(self.calls),210)
        # Historical OHLCV change in the *old* bar must recalculate.
        histories["EQ01","3m"]["bars"][0][4]=100.9
        self.run("EQ01","3m",histories["EQ01","3m"],selected,now+10)
        self.assertEqual(len(self.calls),211)
        self.run("EQ01","3m",histories["EQ01","3m"],selected,now+10)
        self.assertEqual(len(self.calls),211)
        # Completion time changes only the selected 1m source.
        self.run("EQ01","1m",histories["EQ01","1m"],selected,now+60)
        self.assertEqual(len(self.calls),212)
        self.run("EQ01","1m",histories["EQ01","1m"],selected,now+61)
        self.assertEqual(len(self.calls),212)
        # Filter policy, provider generation and source are identity dimensions.
        self.run("EQ01","1m",histories["EQ01","1m"],[{"name":"RSI 14"}],now+61)
        self.assertEqual(len(self.calls),213)
        self.env["provider_generation"][0]=2
        self.run("EQ01","1m",histories["EQ01","1m"],selected,now+61)
        self.assertEqual(len(self.calls),214)
        self.env["prefs"]["source"]="Yahoo Finance"
        self.run("EQ01","1m",histories["EQ01","1m"],selected,now+61)
        self.assertEqual(len(self.calls),215)

    def test_bounded_cache_eviction_after_70_times_three_plus_indexes(self):
        now=1795000000
        history={"source":"Dhan","_scanner_timeframe":"1m","bars":[[now-60,100,101,99,100,1]]}
        for i in range(230):
            self.run(f"EQ{i:03d}","1m",history,[{"name":"MACD"}],now+65)
        self.assertLessEqual(len(self.env["historical_final_replay_cache"]),220)
        self.assertEqual(len(self.calls),230)
        self.assertTrue(all(c["source"]=="Dhan" and c["bars"] is not None for c in self.calls))
        self.assertTrue(all("live_verified" not in c for c in self.calls))


if __name__=="__main__":
    unittest.main()
