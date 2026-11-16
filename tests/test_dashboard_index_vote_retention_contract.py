"""Dashboard three-index historical vote fallback contract (source-only).

The Android Flet UI requires device QA; these guards prevent the previously
confirmed regression where nonempty unusable history hides cached vote bars.
"""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "src" / "main.py"


class DashboardIndexVoteFallbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        cls.target = next(
            node for node in ast.walk(cls.tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "dashboard_market_indices"
        )

    def test_all_three_index_cards_use_same_rendering(self):
        source = ast.get_source_segment(SOURCE.read_text(encoding="utf-8"), self.target)
        self.assertIn('("NIFTY", "BANKNIFTY", "SENSEX")', source)
        self.assertIn("shared_history(index_name)", source)
        self.assertIn("historical_vote_agreement(index_history)", source)

    def test_fallback_handles_nonempty_but_unusable_history(self):
        conditions = [
            node.test for node in ast.walk(self.target)
            if isinstance(node, ast.If)
        ]
        self.assertTrue(any(
            isinstance(test, ast.Compare)
            and isinstance(test.left, ast.Name)
            and test.left.id == "index_agreement"
            and len(test.ops) == 1
            and isinstance(test.ops[0], ast.Is)
            and isinstance(test.comparators[0], ast.Constant)
            and test.comparators[0].value is None
            for test in conditions
        ))
        source = ast.get_source_segment(SOURCE.read_text(encoding="utf-8"), self.target)
        self.assertNotIn('if not index_history.get("bars"):', source)

    def test_previous_vote_never_marked_live(self):
        source = ast.get_source_segment(SOURCE.read_text(encoding="utf-8"), self.target)
        self.assertIn('prior.get("source")=="Dhan"', source)
        self.assertIn('counts=signal_percentages(prior)', source)
        self.assertIn('index_signal_row=vote_display(counts,False)', source)
        self.assertIn('index_signal_row=historical_vote_bar(index_agreement)', source)


if __name__ == "__main__":
    unittest.main()
