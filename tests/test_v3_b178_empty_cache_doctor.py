"""Regression: B178 read-only Doctor must not crash for missing historical bars."""
import ast
import math
from pathlib import Path
import unittest

SOURCE=(Path(__file__).resolve().parents[1]/"src/main.py").read_text()
TREE=ast.parse(SOURCE)
def volume_expr():
    panels=[n for n in ast.walk(TREE) if isinstance(n,ast.FunctionDef)
            and n.name=="filter_five_diagnostic_panel"]
    assert len(panels)==1
    matches=[n for n in ast.walk(panels[0]) if isinstance(n,ast.Assign)
             and any(isinstance(t,ast.Name) and t.id=="valid_volume_rows" for t in n.targets)]
    assert len(matches)==1
    return compile(ast.Expression(matches[0].value),"B178_volume","eval")

class B178OfflineHistoryDoctor(unittest.TestCase):
    def test_no_candle_history_does_not_throw_typeerror(self):
        expr=volume_expr()
        for bars in (None,[],{},()):
            with self.subTest(bars=bars):
                self.assertEqual(eval(expr,{"bars":bars,"math":math}),[])
    def test_real_rows_still_work(self):
        expr=volume_expr()
        rows=[[1780000000,100.,102.,99.,101.,15.],
              [1780000060,101.,103.,99.,102.,20.]]
        self.assertEqual(eval(expr,{"bars":rows,"math":math}),[15.,20.])
    def test_safe_local_failure_diagnostic_remains(self):
        for marker in ('"error_function":fault.name','"error_line":fault.lineno',
                       '"error_message":fault_message','"provider_requests":0',
                       '"orders_sent":0'):
            self.assertIn(marker,SOURCE)
if __name__=="__main__":
    unittest.main()
