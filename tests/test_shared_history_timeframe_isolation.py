"""Execute the real shared_history function with isolated, no-network fixtures."""
import ast
import math
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
import textwrap
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "src" / "main.py"
sys.path.insert(0, str(SOURCE.parent))


def load_selector(*, charts=None, quote=None, scanner=None, source="Dhan"):
    code = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(code)
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "shared_history")
    context = {
        "chart_snapshots": charts or {},
        "quotes": {"NIFTY": quote} if quote is not None else {},
        "candles": {"scanner_chart_NIFTY": scanner} if scanner is not None else {},
        "prefs": {"source": source},
        "provider_generation": [1],
        "scan_generation": [7],
        "valid_candle_history": lambda bars: len(bars or ()) >= 3,
        "math": math,
        "time": time,
        "derived_three_minute_cache": {},
    }
    exec(textwrap.dedent(ast.get_source_segment(code, fn)), context)
    return context["shared_history"]


def history(tf=None, src="Dhan", n=3, generation=7):
    data = {"source": src,
            "bars": [[1000+i*60, 100, 102, 99, 101, 1] for i in range(n)],
            "_scanner_generation": generation}
    if tf is not None:
        data["_scanner_timeframe"] = tf
    return data


class TimeframeHistoryIsolationTests(unittest.TestCase):
    def test_one_minute_does_not_borrow_legacy_five_minute_quote(self):
        select = load_selector(quote=history(None))
        self.assertEqual(select("NIFTY", "1m"), {})
        self.assertEqual(select("NIFTY", "3m"), {})
        self.assertEqual(select("NIFTY").get("source"), "Dhan")

    def test_three_minute_snapshot_is_selected_by_exact_key(self):
        select = load_selector(charts={("NIFTY", "3m", 1): history("3m")})
        self.assertEqual(len(select("NIFTY", "3m")["bars"]), 3)
        self.assertEqual(select("NIFTY", "1m"), {})
        self.assertEqual(select("NIFTY", "5m"), {})

    def test_scanner_three_minute_cannot_replace_superfive_fiveminute(self):
        select = load_selector(
            charts={("NIFTY", "5m", 1): history("5m")},
            scanner=history("3m"),
        )
        self.assertEqual(select("NIFTY")["_scanner_timeframe"], "5m")
        self.assertEqual(select("NIFTY", "3m")["_scanner_timeframe"], "3m")

    def test_wrong_provider_and_generation_fail_closed(self):
        select = load_selector(scanner=history("1m", generation=6),
                               charts={("NIFTY", "1m", 1): history("1m", src="Yahoo Finance")})
        self.assertEqual(select("NIFTY", "1m"), {})

    def test_reuse_cached_dhan_one_minute_to_derive_three_minute(self):
        start = int(datetime(2025, 11, 13, 9, 15,
                             tzinfo=timezone(timedelta(hours=5, minutes=30))).timestamp())
        bars = [[start+i*60, 100, 102, 99, 101, i+1] for i in range(9)]
        source = history("1m")
        source["bars"] = bars
        select = load_selector(charts={("NIFTY", "1m", 1): source})
        derived = select("NIFTY", "3m")
        self.assertEqual(derived["_scanner_timeframe"], "3m")
        self.assertEqual(derived["source"], "Dhan")
        self.assertEqual(derived["bars"][0][0], start)
        self.assertEqual(derived["bars"][0][5], 1+2+3)
        self.assertEqual(len(derived["bars"]), 3)
        self.assertTrue(derived["historical"])
        self.assertFalse(derived["live_verified"])
        self.assertIs(derived, select("NIFTY", "3m"))
        self.assertEqual(select("NIFTY", "5m"), {})

    def test_in_place_last_minute_revision_invalidates_three_minute_cache(self):
        start = int(datetime(2025, 11, 13, 9, 15,
                             tzinfo=timezone(timedelta(hours=5, minutes=30))).timestamp())
        source = history("1m")
        source["bars"] = [[start+i*60, 100, 102, 99, 101, 1] for i in range(9)]
        select = load_selector(charts={("NIFTY", "1m", 1): source})
        old = select("NIFTY", "3m")
        self.assertEqual(old["bars"][-1][4], 101)
        source["bars"][-1][4] = 102
        revised = select("NIFTY", "3m")
        self.assertEqual(revised["bars"][-1][4], 102)
        self.assertIsNot(revised, old)
        self.assertFalse(revised["live_verified"])

    def test_cached_wrong_provider_one_minute_never_derives_dhan_three(self):
        start = int(datetime(2025, 11, 13, 9, 15,
                             tzinfo=timezone(timedelta(hours=5, minutes=30))).timestamp())
        source = history("1m", src="Yahoo Finance")
        source["bars"] = [[start+i*60, 100, 102, 99, 101, 1] for i in range(9)]
        select = load_selector(charts={("NIFTY", "1m", 1): source})
        self.assertEqual(select("NIFTY", "3m"), {})

    def test_three_minute_requires_complete_one_minute_buckets(self):
        start = int(datetime(2025, 11, 13, 9, 15,
                             tzinfo=timezone(timedelta(hours=5, minutes=30))).timestamp())
        source = history("1m")
        source["bars"] = [[start, 100, 102, 99, 101, 1],
                          [start+120, 101, 104, 100, 103, 2]]
        select = load_selector(charts={("NIFTY", "1m", 1): source})
        self.assertEqual(select("NIFTY", "3m"), {})

    def test_reject_unsupported_timeframe(self):
        select = load_selector(quote=history(None))
        self.assertEqual(select("NIFTY", "2m"), {})
        self.assertEqual(select("NIFTY", ""), {})


if __name__ == "__main__":
    unittest.main()
