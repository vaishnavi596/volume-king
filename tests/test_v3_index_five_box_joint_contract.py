"""V3 joint source-level audit for index quote pacing and five-box UI.

No live Dhan, Oracle, Android or trading requests. These tests intentionally
do not claim that five independent directional data feeds exist today.
"""
import ast
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from five_engine import ENGINE_NAMES, compose_snapshot, snapshot_for_display

MAIN=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
GATEWAY=(ROOT/"backend"/"clone_v2_gateway.py").read_text(encoding="utf-8")
TREE=ast.parse(MAIN)


def body(name):
    found=[node for node in ast.walk(TREE)
           if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))
           and node.name==name]
    assert len(found)==1,(name,len(found))
    return ast.get_source_segment(MAIN,found[0])


class IndexFiveBoxJointContract(unittest.TestCase):
    def test_six_slots_are_mounted_in_two_explicit_rows(self):
        chip=body("five_engine_chips")
        self.assertIn('("technical","T")',chip)
        for item in ('("candle","C")','("news","N")','("futures","F")','("options","O")'):
            self.assertIn(item,chip)
        self.assertIn('content=ft.Text("6  —"',chip)
        self.assertIn("ft.Row(cards[:3],spacing=4)",chip)
        self.assertIn("ft.Row(cards[3:],spacing=4)",chip)
        self.assertIn("return ft.Column([",chip)
        self.assertNotIn("return ft.Row(cards,wrap=True",chip)

    def test_wait_cannot_be_promoted_into_fake_live_votes(self):
        self.assertEqual(ENGINE_NAMES,("technical","candle","news","futures","options"))
        rows=snapshot_for_display(compose_snapshot(),now=1800000000)
        self.assertEqual(len(rows["engines"]),5)
        self.assertEqual([e.display()["state"] for e in rows["engines"]],["WAIT"]*5)
        self.assertEqual(rows["combined"]["state"],"WAIT")
        self.assertIn('label=short+" WAIT"',body("five_engine_chips"))

    def test_shared_gateway_serializes_local_burst_but_preserves_provider_quota(self):
        self.assertIn("spacing_remaining=1.05-(now-last_request[0])",GATEWAY)
        self.assertIn("time.sleep(spacing_remaining)",GATEWAY)
        self.assertIn("last_request[0] = now",GATEWAY)
        self.assertIn("provider_cooldown_until[0] = max(",GATEWAY)
        self.assertIn('stage, seconds = "PROVIDER_QUOTA", 30',GATEWAY)
        self.assertIn('"X-BotKing-429-Stage": stage',GATEWAY)
        self.assertIn('market_cache[selection] = (time.monotonic(), payload)',GATEWAY)

    def test_scanner_context_is_not_a_directional_signal(self):
        self.assertIn('row["vote"]=None',body("enrich_context_filter_rows"))
        self.assertIn('name in OPTION_FILTERS',body("enrich_context_filter_rows"))
        chips=body("five_engine_chips")
        # Dashboard defaults to 1m; Watchlist/Scanner pass their own frame.
        # Historical votes remain context, never verified live evidence.
        self.assertIn('if not historical and display_timeframe=="1m":',chips)
        self.assertIn('shared_history(sym,"1m")',chips)
        self.assertIn('if not historical and display_timeframe=="3m":',chips)
        self.assertIn('three=watch_three_minute_signal(sym)',chips)
        self.assertIn('historical_vote_agreement(',chips)
        self.assertIn('display_timeframe is None or raw.get("timeframe")==display_timeframe',chips)
        self.assertIn('exact_frame=display_timeframe or "5m"',chips)
        self.assertIn('read_five_engine_context(sym,exact_frame)',chips)
        self.assertNotIn('read_five_engine_context(sym,"5m")',chips)
        self.assertIn('candle_history=shared_history(sym,candle_tf)',chips)
        self.assertIn('historical=True',body("five_engine_chips"))

if __name__=="__main__":
    unittest.main()
