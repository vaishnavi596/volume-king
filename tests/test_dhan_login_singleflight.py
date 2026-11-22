"""Dhan-only Clone SSK login must serialize quote bootstrap and release locks.

AST checks on real current V3 login. No broker network or credentials.
"""
import ast
from pathlib import Path
import unittest

TREE = ast.parse((Path(__file__).resolve().parents[1]/"src/main.py").read_text())


class DhanLoginSingleflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def method(name):
            found=[n for n in ast.walk(TREE)
                   if isinstance(n,ast.AsyncFunctionDef) and n.name==name]
            assert len(found)==1, name
            return found[0]
        cls.legacy=method("connect_angel")
        cls.clone=method("check_clone_v2_connection")

    def test_legacy_login_is_inert_and_clone_reserves_busy_before_await(self):
        self.assertFalse(any(isinstance(n,ast.Await) for n in ast.walk(self.legacy)))
        body=ast.unparse(self.clone)
        self.assertIn("clone_v2_connect_busy[0] or broker_connect_busy[0]",body)
        self.assertIn("clone_v2_connect_busy[0] = True",body)
        self.assertIn("await asyncio.to_thread(clone_v2_gateway.connect",body)
        self.assertIn("dhan_feed.paced_market_quotes",body)
        assignment=next(n for n in ast.walk(self.clone)
                        if isinstance(n,ast.Assign)
                        and any(ast.unparse(t)=="clone_v2_connect_busy[0]"
                                for t in n.targets)
                        and isinstance(n.value,ast.Constant) and n.value.value is True)
        awaited=[n.lineno for n in ast.walk(self.clone)
                 if isinstance(n,ast.Await)]
        self.assertLess(assignment.lineno,min(awaited))

    def test_clone_always_releases_busy_even_after_network_exception(self):
        clone=self.clone
        finalblocks=[n.finalbody for n in ast.walk(clone)
                     if isinstance(n,ast.Try) and n.finalbody]
        self.assertTrue(any(any(
            isinstance(n,ast.Assign) and
            any(ast.unparse(t)=="clone_v2_connect_busy[0]" for t in n.targets)
            and isinstance(n.value,ast.Constant) and n.value.value is False
            for n in block) for block in finalblocks))
        self.assertIn("server_access.value = ''",ast.unparse(clone).replace('""',"''"))


if __name__=="__main__":
    unittest.main()
