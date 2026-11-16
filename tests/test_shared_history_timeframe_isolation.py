"""Execute the real shared_history function with isolated, no-network fixtures."""
import ast
import math
from pathlib import Path
import textwrap
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "src" / "main.py"


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

    def test_reject_unsupported_timeframe(self):
        select = load_selector(quote=history(None))
        self.assertEqual(select("NIFTY", "2m"), {})
        self.assertEqual(select("NIFTY", ""), {})


if __name__ == "__main__":
    unittest.main()
