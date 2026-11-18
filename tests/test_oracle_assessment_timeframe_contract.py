"""Execute the real Oracle Assessment route in an isolated read-only sandbox.

Proves Android timeframe selector is validated and echoed for both a cached
option evidence response and the fail-closed WAIT placeholder. No Dhan calls.
"""
import ast
import hmac
import re
import unittest
from copy import deepcopy
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

from backend.assessment_filter_adapter import read_only_assessment

SOURCE=(Path(__file__).resolve().parents[1]/"backend"/"server.py").read_text(encoding="utf-8")
TREE=ast.parse(SOURCE)


class FakeHttpException(Exception):
    def __init__(self, code, detail):
        super().__init__(detail)
        self.status_code=code


class OracleAssessmentTimeframeTests(unittest.TestCase):
    def setUp(self):
        methods=[n for n in ast.walk(TREE) if isinstance(n,ast.FunctionDef)
                 and n.name=="botking_read_only_assessment"]
        self.assertEqual(len(methods),1)
        fn=deepcopy(methods[0])
        fn.decorator_list=[]
        mod=ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[]))
        self.observations=[]
        self.cached=None
        def lookup(*args):
            self.observations.append(args)
            return self.cached
        scope={"Optional":Optional,"Header":lambda default=None:default,
               "HTTPException":FakeHttpException,"hmac":hmac,"re":re,
               "pairing_key":"test-key-no-network","date":date,
               "option_evidence_cache":SimpleNamespace(latest=lookup),
               "read_only_assessment":read_only_assessment}
        exec(compile(mod,"<oracle-assessment-contract>","exec"),scope)
        self.handler=scope["botking_read_only_assessment"]

    def test_three_timeframes_are_echoed_without_broker_requests(self):
        for tf in ("1m","3m","5m"):
            with self.subTest(tf=tf):
                result=self.handler("NIFTY",timeframe=tf,x_botking_key="test-key-no-network")
                self.assertEqual(result["timeframe"],tf)
                self.assertEqual(result["collection_status"],"not_configured")
                self.assertFalse(result["signal_eligible"])
                self.assertFalse(result["live_orders_enabled"])
                self.assertEqual(len(result["assessment_filters"]),5)
        self.assertEqual(self.observations,[("NIFTY",None)]*3)

    def test_cached_options_are_still_read_only_and_timeframe_scoped(self):
        self.cached={"pcr":0.81,"max_pain":25100.0,
                     "signal_eligible":False,"freshness":"unverified",
                     "expiry":"2031-11-26","source":"dhan"}
        result=self.handler("NIFTY",expiry="2031-11-26",timeframe="3m",
                            x_botking_key="test-key-no-network")
        self.assertEqual(result["timeframe"],"3m")
        self.assertEqual(result["collection_status"],"partial_unverified")
        self.assertFalse(result["signal_eligible"])
        self.assertIsNone(result["bullish_score"])
        self.assertEqual(self.observations,[("NIFTY","2031-11-26")])

    def test_bad_timeframe_and_missing_auth_rejected_before_cache(self):
        for bad in ("2m","1M","",None if False else [],1,True):
            with self.subTest(bad=repr(bad)):
                with self.assertRaises(FakeHttpException) as cm:
                    self.handler("NIFTY",timeframe=bad,
                                 x_botking_key="test-key-no-network")
                self.assertEqual(cm.exception.status_code,422)
        with self.assertRaises(FakeHttpException) as cm:
            self.handler("NIFTY",timeframe="1m",x_botking_key=None)
        self.assertEqual(cm.exception.status_code,403)
        self.assertEqual(self.observations,[])


if __name__=="__main__":
    unittest.main()
