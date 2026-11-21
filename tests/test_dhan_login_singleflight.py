"""Dhan login must not start overlapping read-only bootstrap requests.

Source-level regression deliberately avoids invoking a broker or credentials.
"""
import ast
import pathlib
import unittest

TREE = ast.parse((pathlib.Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8"))


def subscript_assignment(node, value):
    if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Constant) or node.value.value is not value:
        return False
    return any(isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name)
               and t.value.id == "broker_connect_busy" and isinstance(t.slice, ast.Constant)
               and t.slice.value == 0 for t in node.targets)


class DhanLoginSingleflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        methods = [n for n in ast.walk(TREE) if isinstance(n, ast.AsyncFunctionDef)
                   and n.name == "connect_angel"]
        assert len(methods) == 1, "Expected exactly one login function"
        cls.method = methods[0]
        cls.dhan_branch = next(n for n in cls.method.body
                               if isinstance(n, ast.If)
                               and ast.unparse(n.test) == "broker.value != 'Angel One'")

    def test_dhan_reserves_busy_before_any_network_await(self):
        # This legacy function is permanently fail-closed in V3; the actual
        # Clone V2 SSK login owns the singleflight connection contract.
        self.assertIsInstance(self.method.body[3], ast.Return)
        self.assertFalse(any(isinstance(node, ast.Await)
                             for node in self.method.body[:4]))
        clone = next(n for n in ast.walk(TREE) if isinstance(n, ast.AsyncFunctionDef)
                     and n.name == "check_clone_v2_connection")
        branch = clone.body
        busy_checks = [n for n in branch if isinstance(n, ast.If)
                       and "clone_v2_connect_busy[0]" in ast.unparse(n.test)
                       and "broker_connect_busy[0]" in ast.unparse(n.test)]
        self.assertTrue(busy_checks)
        set_busy = [n for n in branch if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Subscript) and
                            ast.unparse(t) == "clone_v2_connect_busy[0]"
                            for t in n.targets) and
                    isinstance(n.value, ast.Constant) and n.value.value is True]
        self.assertEqual(len(set_busy), 1)
        awaits = [n for n in ast.walk(clone) if isinstance(n, ast.Await)]
        self.assertTrue(awaits)
        self.assertLess(set_busy[0].lineno, min(n.lineno for n in awaits))
        finally_clear = [n for n in ast.walk(clone) if isinstance(n, ast.Assign)
                         and any(isinstance(t, ast.Subscript) and
                                 ast.unparse(t) == "clone_v2_connect_busy[0]"
                                 for t in n.targets) and
                         isinstance(n.value, ast.Constant) and n.value.value is False]
        self.assertTrue(finally_clear)

    def test_dhan_always_releases_busy_even_on_network_failure(self):
        tries = [n for n in self.dhan_branch.body if isinstance(n, ast.Try)]
        release = [n for t in tries for n in t.finalbody
                   if subscript_assignment(n, False)]
        self.assertEqual(len(release), 1)
        self.assertTrue(any(n for n in tries if release[0] in n.finalbody
                            and any(isinstance(x, ast.Await) for x in ast.walk(n))))


if __name__ == "__main__":
    unittest.main()
