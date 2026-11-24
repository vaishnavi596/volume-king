"""B202 physical Doctor 0 candles: manual Scan must reach holiday SSK HIST.

Executes the real nested UI handler with offline fakes. Zero broker requests
from this test and no permission to invent LIVE quote proof.
"""
import ast
import pathlib
import types
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCE=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
TREE=ast.parse(SOURCE)
NODES=[node for node in ast.walk(TREE)
       if isinstance(node,ast.FunctionDef) and node.name=="run_scan"]


class ManualHolidayRunScan(unittest.TestCase):
    def handler(self,*,ssk,connected,closed):
        self.assertEqual(len(NODES),1)
        program=ast.fix_missing_locations(ast.Module(body=[NODES[0]],type_ignores=[]))
        calls=[]
        class Field:
            value=""
        status=Field()
        control=types.SimpleNamespace(value="Dhan")
        feed=types.SimpleNamespace(connected=connected)
        gateway=types.SimpleNamespace(connected=ssk)
        busy=[False]
        page=types.SimpleNamespace(update=lambda:calls.append("update"),
                                   run_task=lambda fn:calls.append(("run_task",fn)))
        def scan_market():
            return None
        env={"prefs":{"source":"Dhan"},"dhan_feed":feed,
             "clone_v2_gateway":gateway,"regular_hours":lambda:not closed,
             "scan_status":status,"scan_busy":busy,"scan_live":types.SimpleNamespace(value=False),
             "scan_result":types.SimpleNamespace(controls=[]),
             "card":lambda x:x,"txt":lambda *x:x,
             "page":page,"scan_market":scan_market}
        exec(compile(program,"src/main.py","exec"),env)
        return env["run_scan"],status,busy,calls

    def test_authenticated_closed_market_manual_scan_dispatches_hist_fetch(self):
        fn,status,busy,calls=self.handler(ssk=True,connected=False,closed=True)
        fn(None)
        self.assertTrue(busy[0])
        self.assertTrue(any(isinstance(c,tuple) and c[0]=="run_task" for c in calls))
        self.assertNotIn("login required",status.value.lower())

    def test_disconnected_closed_market_requires_ssk(self):
        fn,status,busy,calls=self.handler(ssk=False,connected=False,closed=True)
        fn(None)
        self.assertFalse(busy[0])
        self.assertIn("login required",status.value)
        self.assertFalse(any(isinstance(c,tuple) for c in calls))

    def test_open_market_still_requires_quote_proof(self):
        fn,status,busy,calls=self.handler(ssk=True,connected=False,closed=False)
        fn(None)
        self.assertFalse(busy[0])
        self.assertIn("login required",status.value)
        self.assertFalse(any(isinstance(c,tuple) for c in calls))

    def test_verified_feed_may_dispatch_without_closed_session_special_case(self):
        fn,status,busy,calls=self.handler(ssk=True,connected=True,closed=False)
        fn(None)
        self.assertTrue(busy[0])
        self.assertTrue(any(isinstance(c,tuple) for c in calls))

if __name__=="__main__":
    unittest.main()
