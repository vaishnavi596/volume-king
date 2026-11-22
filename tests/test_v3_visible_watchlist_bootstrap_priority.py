"""Offline guard: login candle bootstrap prioritizes visible Watchlist only.
This exercises the source's actual roster statements with no broker calls.
"""
import ast
from pathlib import Path
import unittest

MAIN = Path(__file__).resolve().parents[1] / "src" / "main.py"
SOURCE = MAIN.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def roster_source():
    funcs = [n for n in ast.walk(TREE) if isinstance(n, ast.AsyncFunctionDef)
             and n.name == "watch_login_candle_bootstrap"]
    if len(funcs) != 1:
        raise AssertionError("missing unique watch bootstrap")
    func = funcs[0]
    stmts = [n for n in ast.walk(func) if isinstance(n, ast.Assign)]
    def find(name):
        return next(n for n in stmts if any(isinstance(t, ast.Name) and t.id == name for t in n.targets))
    start = find("visible_group")
    end = find("selected")
    source_lines = SOURCE.splitlines()
    import textwrap
    return textwrap.dedent("\n".join(source_lines[start.lineno - 1:end.end_lineno]))


def roster(groups, active, verified):
    ctx = {"watch_groups": groups, "active_watch": [active],
           "DHAN_VERIFIED_SYMBOLS": verified}
    exec(roster_source(), ctx)
    return ctx["selected"]


class VisibleWatchlistBootstrapPriority(unittest.TestCase):
    def test_visible_group_first_then_remaining_groups_in_original_order(self):
        groups = [["A", "B"], ["C"], ["D", "A"], ["E"], ["F"]]
        self.assertEqual(roster(groups, 2, set("ABCDEF")), ["D", "A", "B", "C", "E", "F"])

    def test_duplicate_and_index_rejected_with_global_seventy_cap(self):
        names = [f"S{i}" for i in range(90)]
        groups = [names[:20], names[20:40], names[40:60],
                  names[60:80], ["NIFTY", "BANKNIFTY", "SENSEX", names[45], *names[80:]]]
        chosen = roster(groups, 4, set(names) | {"NIFTY", "BANKNIFTY", "SENSEX"})
        self.assertEqual(chosen[:11], [names[45], *names[80:]])
        self.assertEqual(len(chosen), 70)
        self.assertEqual(len(set(chosen)), len(chosen))
        self.assertFalse({"NIFTY", "BANKNIFTY", "SENSEX"} & set(chosen))

    def test_invalid_active_tab_falls_back_to_first(self):
        groups = [["A"], ["B"], ["C"]]
        self.assertEqual(roster(groups, 99, set("ABC")), ["A", "B", "C"])
        self.assertEqual(roster(groups, -1, set("ABC")), ["A", "B", "C"])
        self.assertEqual(roster([], 0, set()), [])

    def test_not_in_registry_never_requested(self):
        self.assertEqual(roster([["TCS", "UNKNOWN"], ["INFY"]], 0, {"TCS", "INFY"}),
                         ["TCS", "INFY"])

    def test_pacing_and_history_safety_guards_unchanged(self):
        text = ast.get_source_segment(SOURCE, next(n for n in ast.walk(TREE)
                if isinstance(n, ast.AsyncFunctionDef) and n.name == "watch_login_candle_bootstrap"))
        self.assertIn("await asyncio.sleep(1.5)", text)
        self.assertIn('cooldown_remaining("/dhan/intraday")', text)
        self.assertIn('get_market_data,sym,"1m","2d"', text)
        self.assertIn('historical=True', text)
        self.assertIn('live_verified=False', text)
        self.assertNotIn("asyncio.gather(", text)


if __name__ == "__main__":
    unittest.main()
