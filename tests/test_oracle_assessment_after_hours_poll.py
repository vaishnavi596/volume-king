"""Guard after-hours Oracle Assessment auto-poll without broker requests."""
import ast
import unittest
from pathlib import Path

SOURCE=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
TREE=ast.parse(SOURCE)


class AssessmentAfterHoursPollTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        polls=[node for node in ast.walk(TREE)
               if isinstance(node,ast.AsyncFunctionDef)
               and node.name=="oracle_assessment_poll"]
        assert len(polls)==1
        cls.poll=polls[0]
        cls.block=ast.get_source_segment(SOURCE,cls.poll)

    def test_closed_session_guard_limits_repeat_fetches(self):
        self.assertIn("market_window=refresh_hours()",self.block)
        self.assertIn("oracle_assessment_closed_bootstrap_generation[0]=generation",
                      self.block)
        guard=[node for node in ast.walk(self.poll)
               if isinstance(node,ast.If)
               and "oracle_assessment_closed_bootstrap_generation" in ast.unparse(node.test)]
        self.assertEqual(len(guard),1)
        self.assertTrue(any(isinstance(node,ast.Continue) for node in
                            ast.walk(guard[0])))
        expr=compile(ast.Expression(body=guard[0].test),"<closed-assessment-guard>","eval")
        for last,current,should_skip in ((3,3,True),(3,4,False),
                                         (None,1,False),(0,0,True)):
            with self.subTest(previous=last,generation=current):
                self.assertEqual(eval(expr,{},{
                    "oracle_assessment_closed_bootstrap_generation":[last],
                    "generation":current}),should_skip)

    def test_all_three_dashboard_indexes_use_same_bounded_assessment_lane(self):
        # Exact three-index inventory, regardless of scanner/options/paper
        # selection. This must reuse existing 180s local Assessment GET budget.
        selected = [node for node in ast.walk(self.poll)
                    if isinstance(node, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "selected"
                            for t in node.targets)]
        self.assertEqual(len(selected), 1)
        expr = selected[0].value
        self.assertIsInstance(expr, ast.Call)
        self.assertIsInstance(expr.func, ast.Name)
        self.assertEqual(expr.func.id,"focused_contexts")
        indices=next(k.value for k in expr.keywords if k.arg=="indices")
        self.assertIsInstance(indices,ast.Tuple)
        self.assertEqual(tuple(item.value for item in indices.elts),
                         ("NIFTY","BANKNIFTY","SENSEX"))
        self.assertIn('current[0]', self.block)
        self.assertNotIn('selected.extend(',self.block)
        self.assertIn('now-oracle_assessment_attempts[key]<180', self.block)
        self.assertIn('dhan_feed.assessment,sym,timeframe=tf,expiry=selected_expiry',
                      self.block)
        self.assertNotIn('get_market_data(', self.block)
        self.assertNotIn('dhan_feed.intraday(', self.block)

    def test_bounded_cache_retains_watchlist_roster_and_still_expires(self):
        # Retention capacity must cover up to 70 selected instruments plus
        # indexes/expiry contexts. It does not change the 180s UI freshness TTL.
        self.assertIn("if len(oracle_assessment_cache)>80:", self.block)
        self.assertIn(
            "del oracle_assessment_cache[next(iter(oracle_assessment_cache))]",
            self.block)
        self.assertNotIn("len(oracle_assessment_cache)>16", self.block)
        self.assertIn("now-oracle_assessment_attempts[key]<180", self.block)
        ui=(Path(__file__).resolve().parents[1]/"src"/
            "shared_assessment_ui.py").read_text(encoding="utf-8")
        self.assertIn("def assessment_lines(symbol, cached, *, now=None, max_age=180)",ui)
        self.assertIn("now - fetched > max_age",ui)

    def test_one_after_hours_attempt_does_not_clear_last_good_cache(self):
        # Skipping the repeated poll must preserve historical data for display.
        guard=next(node for node in ast.walk(self.poll)
                   if isinstance(node,ast.If)
                   and "oracle_assessment_closed_bootstrap_generation" in ast.unparse(node.test))
        self.assertFalse(any(isinstance(node,ast.Call)
                             and isinstance(node.func,ast.Attribute)
                             and node.func.attr=="clear"
                             for node in ast.walk(guard)))
        self.assertIn("await asyncio.sleep(15)",ast.get_source_segment(SOURCE,guard))
        self.assertIn("oracle_assessment_attempts[key]=now",self.block)
        self.assertIn("dhan_feed.assessment,sym,timeframe=tf,expiry=selected_expiry",
                      self.block)


if __name__=="__main__":
    unittest.main()
