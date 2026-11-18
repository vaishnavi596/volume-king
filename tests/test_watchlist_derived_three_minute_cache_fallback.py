"""Finite Watchlist regression: completed 3m bars survive transient 1m cache loss.

Runs actual shared_history AST with offline data; no broker or app UI imports.
"""
import ast
import math
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from candle_retention import valid_candle_history

TREE = ast.parse((ROOT / "src" / "main.py").read_text(encoding="utf-8"))
NODES = [n for n in ast.walk(TREE)
         if isinstance(n, ast.FunctionDef) and n.name == "shared_history"]
assert len(NODES) == 1


def make_resolver(generation=1, source="Dhan"):
    scope = {
        "prefs": {"source": source},
        "provider_generation": [generation],
        "scan_generation": [1],
        "chart_snapshots": {},
        "quotes": {},
        "candles": {},
        "derived_three_minute_cache": {},
        "time": time,
        "math": math,
        "valid_candle_history": valid_candle_history,
    }
    exec(compile(ast.Module(body=[NODES[0]], type_ignores=[]),
                 "<watch-shared-history>", "exec"), scope)
    return scope, scope["shared_history"]


def complete_bars(count=36):
    base = 1795000000
    return [[base+i*180, 100+i, 101+i, 99+i, 100+i, 1200]
            for i in range(count)]


class WatchlistThreeMinuteFallbackTests(unittest.TestCase):
    def test_valid_completed_derived_history_survives_missing_one_minute(self):
        scope, history = make_resolver()
        rows = complete_bars()
        previous = {"source": "Dhan", "bars": rows,
                    "_scanner_timeframe": "3m", "historical": True,
                    "live_verified": False, "freshness": "historical_unverified"}
        scope["derived_three_minute_cache"]["RELIANCE"] = ((1, "source-identity"), previous)
        got = history("RELIANCE", "3m")
        self.assertEqual(got["bars"], rows)
        self.assertTrue(got["cached"])
        self.assertTrue(got["_candle_retained"])
        self.assertEqual(got["freshness"], "historical_unverified")
        self.assertFalse(got["live_verified"])
        self.assertNotIn("cached", previous)
        self.assertEqual(history("RELIANCE", "1m"), {})

    def test_prior_generation_or_foreign_provider_does_not_leak(self):
        for gen, provider in ((2, "Dhan"), (1, "Yahoo Finance"),
                              (1, "Broker API")):
            with self.subTest(gen=gen, provider=provider):
                scope, history = make_resolver(generation=gen, source=provider)
                scope["derived_three_minute_cache"]["RELIANCE"] = (
                    (1, "old"), {"source": "Dhan", "bars": complete_bars(),
                                  "_scanner_timeframe": "3m"})
                self.assertEqual(history("RELIANCE", "3m"), {})

    def test_invalid_or_short_cache_never_appears(self):
        for rows in ([], complete_bars(2), [[1,2,3,4,5,6]]*36):
            with self.subTest(length=len(rows)):
                scope, history = make_resolver()
                scope["derived_three_minute_cache"]["TCS"] = (
                    (1, "old"), {"source": "Dhan", "bars": rows,
                                  "_scanner_timeframe": "3m"})
                self.assertEqual(history("TCS", "3m"), {})


if __name__ == "__main__":
    unittest.main()
