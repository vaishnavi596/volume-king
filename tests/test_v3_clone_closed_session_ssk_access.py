"""Actual phone Clone SSK closed-session contract: no holiday quote fanout.

The market-data login path remains separately fail-closed until genuine Dhan
price proof; the SSK status cannot claim any LIVE evidence.
"""
import ast
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
MAIN=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
TREE=ast.parse(MAIN)

class CloneClosedSessionGatewayTests(unittest.TestCase):
    def test_holiday_ssk_handshake_short_circuits_quote_source_proof(self):
        funcs=[n for n in ast.walk(TREE) if isinstance(n,ast.AsyncFunctionDef)
               and n.name=="check_clone_v2_connection"]
        self.assertEqual(len(funcs),1)
        body=ast.get_source_segment(MAIN,funcs[0])
        auth=body.index('building_doctor.milestone("gateway_authorized")')
        session_gate=body.index("if not regular_hours():",auth)
        no_quote=body.index("return",session_gate)
        quote=body.index("dhan_feed.paced_market_quotes",auth)
        activation=body.index("dhan_feed.activate_with_quote(proof)",auth)
        self.assertLess(auth,session_gate)
        self.assertLess(session_gate,no_quote)
        self.assertLess(no_quote,quote)
        self.assertLess(quote,activation)
        branch=body[session_gate:no_quote]
        self.assertIn("equity_session_closed_detail()",branch)
        self.assertIn("market-data quotes unverified",branch)
        self.assertIn("HIST cache only",branch)
        self.assertIn("LIVE OFF",branch)
        self.assertNotIn("provider_changed(",branch)
        self.assertNotIn("dhan_feed.activate_with_quote",branch)
        self.assertNotIn("provider_generation",branch)

    def test_open_session_proof_still_fail_closed(self):
        funcs=[n for n in ast.walk(TREE) if isinstance(n,ast.AsyncFunctionDef)
               and n.name=="check_clone_v2_connection"]
        body=ast.get_source_segment(MAIN,funcs[0])
        self.assertIn('if not proof:',body)
        self.assertIn('raise FeedError("Clone B3 Dhan quote proof unavailable; SSK-only connection")',body)
        self.assertIn("dhan_feed.activate_with_quote(proof)",body)
        self.assertIn("building_doctor.milestone(\"quotes_response_received\")",body)
        self.assertIn("server_access.value=\"\"",body)

if __name__=="__main__":
    unittest.main()
