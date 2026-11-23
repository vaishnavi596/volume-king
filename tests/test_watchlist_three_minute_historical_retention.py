"""Exercise the real nested Watchlist 3m function using mocked offline data.

No broker transport, no UI framework, no network calls. Test real retention policy
and historical safety rather than merely searching for source text.
"""
import ast
import math
import sys
import textwrap
import time
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from candle_retention import retain_last_filter_votes

SOURCE=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
NODE=next(node for node in ast.walk(ast.parse(SOURCE)) if isinstance(node,ast.FunctionDef)
          and node.name=="watch_three_minute_signal")
FUNCTION=textwrap.dedent(ast.get_source_segment(SOURCE,NODE))


class WatchThreeMinuteHistoricalRetentionTests(unittest.TestCase):
    def setup_function(self, *, history=None, usable=True, current_votes=None):
        prefs={"source":"Dhan","confidence":75}
        chosen=["RSI","MACD"]
        modes={"RSI":"Analysis","MACD":"Analysis"}
        generated=[1]
        cache={}
        calls=[]
        published=[]
        def publish_five_engine_historical(sym,tf,result):
            # Real publisher is tested separately; this harness only checks
            # that the completed 3m analysis reaches its cache handoff.
            published.append((sym,tf,dict(result)))
            return True
        now=time.time()
        bars=history if history is not None else {}
        def quality(rows,seconds,now=None):
            calls.append("quality")
            return {"usable":usable,"bars":rows}
        def analyze(rows,selected,tf):
            calls.append("analyze")
            return {"votes":current_votes if current_votes is not None
                    else [{"name":"RSI","vote":-1},{"name":"MACD","vote":-1}],
                    "timestamp":now-300,"score":80,"bias":"BEARISH"}
        def percentages(row):
            votes=row.get("votes") or []
            bull=sum(v.get("vote")==1 for v in votes if isinstance(v,dict))
            bear=sum(v.get("vote")==-1 for v in votes if isinstance(v,dict))
            return (100*bull//(bull+bear),100*bear//(bull+bear),bull+bear) if bull+bear else None
        scope={"prefs":prefs,"filter_selected":chosen,"filter_modes":modes,
               "provider_generation":generated,"watch_three_minute_cache":cache,
               "shared_history":lambda sym,tf:bars,"time":time,"math":math,
               "quality_check":quality,"analyze":analyze,
               "signal_percentages":percentages,"retain_last_filter_votes":retain_last_filter_votes,
               "log_error":lambda label,exc:calls.append("error"),
               "publish_five_engine_historical":publish_five_engine_historical,
               "published_historical":published}
        exec(compile(FUNCTION,str(ROOT/"src"/"main.py"),"exec"),scope)
        return scope,calls

    @staticmethod
    def store_prior(scope, *, source="Dhan", votes=None):
        config=(scope["provider_generation"][0],tuple(scope["filter_selected"]),
                tuple(sorted(scope["filter_modes"].items())),scope["prefs"]["confidence"])
        old={"source":source,"symbol":"RELIANCE","timeframe":"3m",
             "timestamp":15000.0,"historical":True,"live_verified":False,
             "freshness":"historical_unverified","score":75,"bias":"BULLISH",
             "votes":votes if votes is not None else
                 [{"name":"RSI","vote":1},{"name":"MACD","vote":-1}]}
        scope["watch_three_minute_cache"]["RELIANCE"]=(config+("old_revision",30,15000),old)
        return old

    def test_no_prior_returns_wait_without_fabricated_votes(self):
        scope,calls=self.setup_function()
        row=scope["watch_three_minute_signal"]("RELIANCE")
        self.assertEqual(row["bias"],"WAIT")
        self.assertFalse(row.get("votes"))
        self.assertFalse(calls)

    def test_missing_history_retains_last_hist_votes_but_never_live(self):
        scope,calls=self.setup_function()
        old=self.store_prior(scope)
        row=scope["watch_three_minute_signal"]("RELIANCE")
        self.assertEqual(row["votes"],old["votes"])
        self.assertEqual(row["timestamp"],old["timestamp"])
        self.assertEqual(row["timeframe"],"3m")
        self.assertTrue(row["_last_votes_retained"])
        self.assertTrue(row["historical"])
        self.assertFalse(row["live_verified"])
        self.assertEqual(row["freshness"],"unverified")
        self.assertEqual(row["bias"],"WAIT")
        self.assertEqual(row["score"],0)
        self.assertFalse(calls)  # no provider requests or analysis calls

    def test_context_mismatch_cannot_reuse_previous_votes(self):
        for change in ("generation","filter","mode","confidence","provider"):
            with self.subTest(change=change):
                scope,_=self.setup_function()
                self.store_prior(scope)
                if change=="generation":
                    scope["provider_generation"][0]=2
                elif change=="filter":
                    scope["filter_selected"][:]=["RSI"]
                elif change=="mode":
                    scope["filter_modes"]["RSI"]="Chart"
                elif change=="confidence":
                    scope["prefs"]["confidence"]=90
                else:
                    scope["prefs"]["source"]="Yahoo Finance"
                row=scope["watch_three_minute_signal"]("RELIANCE")
                self.assertEqual(row["bias"],"WAIT")
                self.assertFalse(row.get("votes"))

    def test_prior_from_other_source_or_without_direction_is_not_retained(self):
        for source,votes in (
            ("Yahoo Finance",[{"name":"RSI","vote":1},{"name":"MACD","vote":-1}]),
            ("Dhan",[{"name":"RSI","vote":None},{"name":"MACD","vote":None}]),
        ):
            with self.subTest(source=source,votes=votes):
                scope,_=self.setup_function()
                self.store_prior(scope,source=source,votes=votes)
                row=scope["watch_three_minute_signal"]("RELIANCE")
                self.assertEqual(row["bias"],"WAIT")
                self.assertFalse(row.get("votes"))

    def test_bad_new_history_quality_keeps_historical_votes(self):
        now=time.time()
        # One completed OHLCV bar is insufficient; quality check must reject it.
        scope,calls=self.setup_function(history={"source":"Dhan",
              "bars":[(now-600,100,101,99,100,100)],"candle_fetched_at":now},
              usable=False)
        old=self.store_prior(scope)
        row=scope["watch_three_minute_signal"]("RELIANCE")
        self.assertEqual(row["votes"],old["votes"])
        self.assertTrue(row["historical"])
        self.assertEqual(row["bias"],"WAIT")
        self.assertIn("quality",calls)
        self.assertNotIn("analyze",calls)

    def test_valid_new_three_minute_votes_replace_retained_snapshot(self):
        now=time.time()
        new_votes=[{"name":"RSI","vote":-1},{"name":"MACD","vote":-1}]
        scope,calls=self.setup_function(
            history={"source":"Dhan",
                     "bars":[(now-600,100,101,99,100,100)],"candle_fetched_at":now},
            usable=True,current_votes=new_votes)
        self.store_prior(scope)
        row=scope["watch_three_minute_signal"]("RELIANCE")
        self.assertEqual(row["votes"],new_votes)
        self.assertEqual(row["bias"],"BEARISH")
        self.assertFalse(row.get("_last_votes_retained",False))
        self.assertTrue(row["historical"])
        self.assertFalse(row["live_verified"])
        self.assertIn("analyze",calls)
        self.assertNotIn("error",calls)
        self.assertEqual(len(scope["published_historical"]),1)
        symbol,tf,snapshot=scope["published_historical"][0]
        self.assertEqual((symbol,tf),("RELIANCE","3m"))
        self.assertEqual(snapshot["votes"],new_votes)
        self.assertTrue(snapshot["historical"])
        self.assertFalse(snapshot["live_verified"])


if __name__=="__main__":
    unittest.main()
