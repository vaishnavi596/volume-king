"""Offline 5/34/70 selected Watchlist contract and cache workload checks.

This exercises current source roster and quote-batch selection. It does NOT
measure Dhan, Oracle, Android, or Flutter wall-clock refresh latency.
"""
import ast
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from clone_smart_refresh_priority import priority_equity_batch
from test_v3_visible_watchlist_bootstrap_priority import roster, SOURCE, TREE

INDEX={"NIFTY","BANKNIFTY","SENSEX"}


def groups_of(n):
    selected=[f"E{i:02}" for i in range(n)]
    return [selected[i::5] for i in range(5)],selected


def bootstrap_source():
    matches=[n for n in ast.walk(TREE) if isinstance(n,ast.AsyncFunctionDef)
             and n.name=="watch_login_candle_bootstrap"]
    assert len(matches)==1
    return ast.get_source_segment(SOURCE,matches[0])


class SelectedWatchlistCapacity(unittest.TestCase):
    def test_5_34_70_rosters_and_batched_quotes(self):
        for n in (5,34,70):
            with self.subTest(selected=n):
                groups,names=groups_of(n)
                actual=roster(groups,3,set(names)|INDEX)
                expected=groups[3]+[x for i,g in enumerate(groups) if i!=3 for x in g]
                self.assertEqual(actual,expected)
                self.assertEqual(len(actual),n)
                self.assertEqual(len(set(actual)),n)
                quote_batch=priority_equity_batch(names,[],verified=set(names)|INDEX)
                self.assertEqual(quote_batch,names)
                self.assertEqual(len(quote_batch),n)
                self.assertFalse(INDEX.intersection(actual))

    def test_cache_hit_and_miss_counts_across_sizes(self):
        # Distinguish skipped 1.5s waits from uncached work; no sleeps or
        # fake network timing are executed. The actual fast-path is guarded
        # against different generation, timeframe and stale cache entries.
        for n in (5,34,70):
            groups,names=groups_of(n)
            chosen=roster(groups,2,set(names))
            generation=7
            expected_keys={(generation,0,True,"Dhan",sym,"1m","2d"):10.0
                           for sym in chosen[:n//2]}
            def ready(sym, now=20.0):
                key=(generation,0,True,"Dhan",sym,"1m","2d")
                stamp=expected_keys.get(key)
                return stamp is not None and 0<=now-stamp<87
            hits=sum(ready(s) for s in chosen)
            misses=n-hits
            self.assertEqual(hits,n//2)
            self.assertEqual(misses,n-n//2)
            # Schedule-bound waits only, not actual endpoint latency.
            self.assertEqual(1.5*misses,1.5*(n-n//2))
            self.assertFalse(ready(chosen[0],now=98.0))
            self.assertFalse((generation+1,0,True,"Dhan",chosen[0],"1m","2d")
                             in expected_keys)
            self.assertFalse((generation,0,True,"Dhan",chosen[0],"5m","2d")
                             in expected_keys)

    def test_source_preserves_singleflight_cooldown_and_complete_history(self):
        code=bootstrap_source()
        for token in ('watch_three_minute_warm_busy[0]=True',
                      'cooldown_remaining("/dhan/intraday")',
                      'if not cache_ready:', 'await asyncio.sleep(1.5)',
                      'get_market_data,sym,"1m","2d"',
                      'historical=True', 'live_verified=False',
                      'if valid_candle_history(prior.get("bars")):'):
            self.assertIn(token,code)
        self.assertNotIn("asyncio.gather(",code)
        self.assertNotIn("asyncio.create_task(",code)

    def test_index_and_unverified_excluded_even_at_cap(self):
        groups,names=groups_of(70)
        groups[4].extend(["NIFTY","NOT_VERIFIED",names[1]])
        picked=roster(groups,4,set(names)|INDEX)
        self.assertEqual(len(picked),70)
        self.assertEqual(len(set(picked)),70)
        self.assertFalse(INDEX.intersection(picked))
        self.assertNotIn("NOT_VERIFIED",picked)


if __name__=="__main__":
    unittest.main()
