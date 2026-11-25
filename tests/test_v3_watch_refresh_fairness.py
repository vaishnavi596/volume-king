import ast
import unittest
from pathlib import Path

class WatchRefreshFairness(unittest.TestCase):
    def test_oldest_attempt_first_stable_and_generation_scoped(self):
        tree=ast.parse((Path(__file__).resolve().parents[1]/"src/main.py").read_text())
        node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="watch_refresh_priority")
        ns={"shared_history":lambda sym,tf:{}, "watch_three_minute_warm_attempts":{(1,"RELIANCE"):100,(1,"TCS"):50,(0,"INFY"):200}}
        exec(compile(ast.Module(body=[node],type_ignores=[]),"<watch priority>","exec"),ns)
        order=ns["watch_refresh_priority"]
        self.assertEqual(order(["RELIANCE","TCS","INFY","ITC"],1),["INFY","ITC","TCS","RELIANCE"])
        self.assertEqual(order(["RELIANCE","TCS"],2),["RELIANCE","TCS"])
        ns["watch_three_minute_warm_attempts"][(1,"INFY")]=150
        self.assertEqual(order(["RELIANCE","TCS","INFY"],1),["TCS","RELIANCE","INFY"])

    def test_both_periodic_lanes_use_priority_but_closed_pass_unchanged(self):
        src=(Path(__file__).resolve().parents[1]/"src/main.py").read_text()
        self.assertIn("if not explicit_closed:\n            selected=watch_refresh_priority([sym for sym in all_watch_symbols()",src)
        self.assertIn("                selected=watch_refresh_priority(selected,generation)\n                for sym in selected:",src)
