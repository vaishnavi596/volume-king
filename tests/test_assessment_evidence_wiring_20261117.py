"""Static regression for the single-provider-call assessment handoff."""
import ast
from pathlib import Path
import unittest


class AssessmentEvidenceWiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = (Path(__file__).resolve().parents[1] / "backend" / "server.py").read_text()
        cls.tree = ast.parse(source)

    def test_option_chain_populates_cache_and_assessment_only_reads(self):
        funcs = {node.name: node for node in ast.walk(self.tree)
                 if isinstance(node, ast.FunctionDef)}
        chain = funcs["dhan_option_chain"]
        assessment = funcs["botking_read_only_assessment"]
        chain_calls = [n for n in ast.walk(chain) if isinstance(n, ast.Call)]
        assess_calls = [n for n in ast.walk(assessment) if isinstance(n, ast.Call)]
        self.assertEqual(sum(isinstance(c.func, ast.Attribute) and
                             c.func.attr == "option_chain" for c in chain_calls), 1)
        self.assertTrue(any(isinstance(c.func, ast.Attribute) and
                            c.func.attr == "put" for c in chain_calls))
        self.assertTrue(any(isinstance(c.func, ast.Attribute) and
                            c.func.attr == "latest" for c in assess_calls))
        self.assertTrue(any(isinstance(c.func, ast.Name) and
                            c.func.id == "read_only_assessment" for c in assess_calls))
        self.assertFalse(any(isinstance(c.func, ast.Attribute) and
                             c.func.attr in ("option_chain", "ltp", "intraday")
                             for c in assess_calls))


if __name__ == "__main__":
    unittest.main()
