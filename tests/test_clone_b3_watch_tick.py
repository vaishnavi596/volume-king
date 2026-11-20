"""Static regression guard for B3 watchlist tick signal reuse."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "main.py"


class WatchTickSignalReuse(unittest.TestCase):
    def test_one_signal_analysis_call_per_visible_symbol(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        functions = [n for n in ast.walk(tree)
                     if isinstance(n, ast.AsyncFunctionDef)
                     and n.name == "watch_visible_tick"]
        self.assertEqual(len(functions), 1)
        fn = functions[0]
        calls = [n for n in ast.walk(fn)
                 if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name)
                 and n.func.id == "watch_three_minute_signal"]
        self.assertEqual(len(calls), 1,
                         "Watchlist tick should analyze each symbol only once")
        text = ast.get_source_segment(SOURCE.read_text(encoding="utf-8"), fn)
        self.assertIn("tick_signals[sym]", text)
        self.assertIn("signal_row=tick_signals[sym]", text)
        self.assertIn("row=signal_row", text)


if __name__ == "__main__":
    unittest.main()
