"""Read-only Watchlist stale transitions on 2-second local UI observation."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

SRC=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text("utf-8")
TREE=ast.parse(SRC)

def actual_age_flags(quotes,signals,engines):
    matches=[node for node in ast.walk(TREE) if isinstance(node,ast.FunctionDef)
             and node.name=="watch_cell_age_flags"]
    assert len(matches)==1
    namespace={"quotes":quotes,"watch_signal_cache":signals,"watch_three_minute_signal":lambda sym: signals.get(sym,{}),
               "five_engine_snapshots":engines,
               "timeframe_spec":lambda _tf:{"fresh_seconds":300},
               "time":SimpleNamespace(time=lambda:1000)}
    exec(compile(ast.Module(body=matches,type_ignores=[]),"<app-watch-age-flags>","exec"),namespace)
    return namespace["watch_cell_age_flags"]

class WatchlistAgeTransitionTests(unittest.TestCase):
    def test_same_cached_quote_becomes_stale_without_request(self):
        fn=actual_age_flags({"HDFCBANK":{"fetched_at":939.95}},
                            {"HDFCBANK":{"timestamp":699.95}},
                            {"HDFCBANK":{"engines":[SimpleNamespace(eligible=True,timestamp=699.95)]}})
        self.assertEqual(fn("HDFCBANK",now_epoch=999.90),(False,False,(False,)))
        self.assertEqual(fn("HDFCBANK",now_epoch=1000),(True,True,(True,)))

    def test_missing_unverified_timestamps_do_not_crash_or_request(self):
        fn=actual_age_flags({"RELIANCE":{"fetched_at":None}},
                            {"RELIANCE":{"timestamp":"unverified"}},
                            {"RELIANCE":{"engines":[SimpleNamespace(eligible=False,timestamp=None)]}})
        self.assertEqual(fn("RELIANCE",now_epoch=1000),(False,False,(False,)))
        self.assertEqual(fn("UNKNOWN",now_epoch=1000),(False,False,()))

    def test_visible_watchlist_signatures_include_age_transition(self):
        block=SRC.split("    async def watch_visible_tick():",1)[1].split(
            "    def watchlist():",1)[0]
        self.assertGreaterEqual(block.count("watch_cell_age_flags(sym)"),2)
        self.assertNotIn("dhan_feed.batch_quotes(",block)
        self.assertNotIn("request_view_refresh(4)",block)
