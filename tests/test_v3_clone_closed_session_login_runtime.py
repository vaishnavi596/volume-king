"""Runtime execution of real nested Clone login on holiday vs open session.

Offline mocked phone dependencies. No Dhan, Oracle, network or token calls.
"""
import ast
import asyncio
import pathlib
import types
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
SRC=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
TREE=ast.parse(SRC)
NODES=[n for n in ast.walk(TREE) if isinstance(n,ast.AsyncFunctionDef)
       and n.name=="check_clone_v2_connection"]

class FakeDoctor:
    def __init__(self):
        self.events=[]
    def start_login(self): self.events.append("start_login")
    def milestone(self,step): self.events.append(step)

class FakeField:
    def __init__(self,value=""):
        self.value=value
        self.color=None

class HolidaySSKRuntimeTests(unittest.IsolatedAsyncioTestCase):
    def setup_flow(self,market_open=False,authenticated=True):
        self.assertEqual(len(NODES),1)
        program=ast.fix_missing_locations(ast.Module(body=[NODES[0]],type_ignores=[]))
        calls=[]
        async def async_to_thread(fn,*args):
            calls.append((fn.__name__,args))
            return fn(*args)
        async_api=types.SimpleNamespace(to_thread=async_to_thread)
        def connect(endpoint,key):
            return {"status":"connected_read_only" if authenticated else "not_authorized"}
        def quote(*args):
            if not market_open:
                raise AssertionError("Unexpected LIVE quote request in holiday/offline route")
            return {}
        def activate(*args):
            raise AssertionError("Unexpected LIVE activation")
        doctor=FakeDoctor()
        server_access=FakeField("secret-stays-private")
        status=FakeField()
        busy=[False]
        page=types.SimpleNamespace(update=lambda:None)
        class FeedError(Exception):pass
        ctx={
            "clone_v2_connect_busy":busy,"broker_connect_busy":[False],
            "building_doctor":doctor,"api_url":FakeField("https://example.org"),
            "server_access":server_access,"connection_status":status,"GOLD":"gold",
            "RED":"red","GREEN":"green","page":page,"asyncio":async_api,
            "clone_v2_gateway":types.SimpleNamespace(connect=connect),
            "dhan_feed":types.SimpleNamespace(paced_market_quotes=quote,
                                               activate_with_quote=activate),
            "regular_hours":lambda:market_open,
            "all_watch_symbols":lambda: ["RELIANCE"],
            "equity_session_closed_detail":lambda:" • NSE/BSE trading holiday",
            "FeedError":FeedError,"log_error":lambda *a:None,
        }
        exec(compile(program,str(ROOT/"src"/"main.py"),"exec"),ctx)
        return ctx["check_clone_v2_connection"],calls,status,server_access,busy,doctor

    async def test_authenticated_closed_market_is_ssk_only_and_no_quote_request(self):
        f,calls,status,server,busy,doctor=self.setup_flow()
        await f()
        self.assertEqual([x[0] for x in calls],["connect"])
        self.assertIn("Clone SSK connected",status.value)
        self.assertIn("NSE/BSE trading holiday",status.value)
        self.assertIn("HIST cache only",status.value)
        self.assertIn("LIVE OFF",status.value)
        self.assertEqual(status.color,"gold")
        self.assertEqual(server.value,"")
        self.assertFalse(busy[0])
        self.assertIn("gateway_authorized_closed_session",doctor.events)
        self.assertNotIn("login_failed",doctor.events)

    async def test_failed_ssk_authentication_does_not_enter_closed_session(self):
        f,calls,status,server,busy,doctor=self.setup_flow(authenticated=False)
        await f()
        self.assertEqual([x[0] for x in calls],["connect"])
        self.assertEqual(status.color,"red")
        self.assertIn("read-only authorization unavailable",status.value)
        self.assertNotIn("gateway_authorized_closed_session",doctor.events)
        self.assertEqual(server.value,"")
        self.assertFalse(busy[0])

    async def test_market_open_reaches_quote_proof_gate_without_false_activation(self):
        f,calls,status,server,busy,doctor=self.setup_flow(market_open=True)
        await f()
        self.assertEqual([x[0] for x in calls],["connect","quote"])
        self.assertIn("quote proof unavailable",status.value)
        self.assertEqual(status.color,"red")
        self.assertNotIn("gateway_authorized_closed_session",doctor.events)
        self.assertNotIn("HIST cache only",status.value)
        self.assertFalse(busy[0])
        self.assertEqual(server.value,"")

if __name__=="__main__":
    unittest.main()
