"""Behavioral tests for the actual closed-market bootstrap condition.

Expression evaluated from the checked-in app source, avoiding a fake,
reimplemented guard that could pass while the Android callsite is broken.
"""
import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
TREE=ast.parse(SRC)

def bootstrap_expr(name):
    matches=[node.value for node in ast.walk(TREE)
             if isinstance(node,ast.Assign)
             and any(isinstance(target,ast.Name) and target.id==name
                     for target in node.targets)]
    if len(matches)!=1:
        raise AssertionError(f"Expected exactly one {name} assignment")
    return compile(ast.Expression(body=matches[0]),"<actual-app-bootstrap-gate>","eval")

class BootstrapBehaviorTests(unittest.TestCase):
    def test_stale_saved_price_does_not_cancel_failed_login_retry(self):
        expression=bootstrap_expr("closing_bootstrap")
        for closed, attempted, successful, expected in [
            (True,None,None,True),
            (True,None,9,True),
            (True,None,10,False),
            (True,10,None,False),
            (False,None,None,False),
        ]:
            with self.subTest(closed=closed,attempted=attempted,successful=successful):
                state={"refresh_hours":lambda:not closed,
                       "closed_equity_bootstrap_generation":[attempted],
                       "watch_batch_success_generation":[successful],
                       "provider_generation":[10],
                       # A saved price must not influence session-success gating.
                       "quotes":{"RELIANCE":{"source":"Dhan","price":1339.70}}}
                self.assertIs(eval(expression,state),expected)

    def test_index_first_load_stays_separate_from_equity_and_once_per_generation(self):
        # Evaluate ALL prerequisite expressions from the real Android source,
        # not a rewritten model of the condition. Cached prices are deliberately
        # present even when the latest login only loaded one or two indices.
        expressions={key:bootstrap_expr(key) for key in
            ("same_index_login","index_loaded_this_login",
             "index_login_recovery_ready","closed_index_bootstrap")}
        old_prices={"NIFTY":{"source":"Dhan","price":25144.3},
                    "BANKNIFTY":{"source":"Dhan","price":61034.1},
                    "SENSEX":{"source":"Dhan","price":81592.45}}
        for closed,attempted,prices,generation,state,counts,expected in (
            (True,None,{},10,"PARTIAL",(2,3),True),
            (True,None,old_prices,10,"PARTIAL",(2,3),True),
            (True,None,old_prices,10,"LOADED",(3,3),False),
            (True,None,{},10,"LOADING",None,False),
            (True,None,{},10,"FAILED",(0,3),True),
            (True,None,{},10,"COOLDOWN",(0,3),True),
            (True,10,{},10,"FAILED",(0,3),False),
            (False,None,{},10,"FAILED",(0,3),False),
            (True,None,{},9,"FAILED",(0,3),False),
        ):
            with self.subTest(closed=closed,attempted=attempted,
                              login_generation=generation,state=state):
                bootstrap=type("Bootstrap",(),{
                    "generation":generation,"stages":{"indices":state},
                    "counts":{"indices":counts} if counts is not None else {}})()
                env={"refresh_hours":lambda:not closed,
                     "closed_index_bootstrap_generation":[attempted],
                     "provider_generation":[10],
                     "login_bootstrap":bootstrap,"quotes":prices}
                for name,expression in expressions.items():
                    env[name]=eval(expression,env)
                self.assertIs(env["closed_index_bootstrap"],expected)

    def test_ui_shows_actual_quote_check_even_when_closed_timer_is_paused(self):
        block=SRC.split("    def watchlist():",1)[1].split("    symbol=ft.Dropdown",1)[0]
        self.assertIn('ft.Text("Quote check • "+watch_batch_status[0]',block)
        self.assertIn('ft.TextButton("Refresh data"',block)
        self.assertIn('ft.TextOverflow.ELLIPSIS',block)

    def test_login_snapshot_status_is_visible_without_waiting_for_next_poll(self):
        block=SRC.split("    async def connect_angel():",1)[1].split("    def pairing_diagnostic(",1)[0] if "    def pairing_diagnostic(" in SRC.split("    async def connect_angel():",1)[1] else SRC.split("    async def connect_angel():",1)[1].split("    def provider_changed(",1)[0]
        self.assertIn('("Login Dhan direct batch • " if direct_login_batch else "Login Oracle snapshot • ")',block)
        self.assertIn('"Login snapshot failed • "+safe_error(exc)',block)
        self.assertIn('watch_batch_last_success[0]=time.monotonic()',block)
        self.assertIn('last valid prices retained',block)

    def test_market_open_cadence_and_cooldown_unchanged(self):
        poll=SRC.split("    async def dhan_quote_poll():",1)[1].split("    # The Watchlist observes",1)[0]
        index=SRC.split("    async def dhan_index_poll():",1)[1].split("    page.run_task(dhan_index_poll)",1)[0]
        self.assertIn('app_active[0] and refresh_hours() and prefs.get("source")=="Dhan"',poll)
        self.assertIn('app_active[0] and refresh_hours() and prefs.get("source")=="Dhan"',index)
        self.assertIn('>=60',poll)
        self.assertIn('remaining=dhan_feed.cooldown_remaining("/v2/snapshot")',poll)
        self.assertIn('closed_equity_bootstrap_generation[0]=provider_generation[0]',poll)

if __name__=="__main__":
    unittest.main()
