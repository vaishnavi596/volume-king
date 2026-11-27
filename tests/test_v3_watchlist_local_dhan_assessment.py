"""Run the mounted Oracle Watchlist fallback with synthetic cache-only fixtures."""
import ast
import pathlib
import unittest
from types import SimpleNamespace

MAIN = pathlib.Path(__file__).resolve().parents[1] / "src" / "main.py"
OLD_PLACEHOLDER = "Oracle 4 factors / 5 filters • WAIT • server producer not configured"

class WatchlistLocalDhanFallbackTests(unittest.TestCase):
    def _invoke(self, three, *, surface="watchlist", lines=None):
        source = MAIN.read_text()
        tree = ast.parse(source, filename=str(MAIN))
        fn = next(node for node in ast.walk(tree)
                  if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                  and node.name == "oracle_assessment_notes")
        module = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
        calls = []
        def local_signal(symbol):
            calls.append(symbol)
            return dict(three)
        env = {
            "provider_generation": [7],
            "oracle_assessment_cache_generation": [7],
            "oracle_assessment_cache": {(7, "RELIANCE", "3m", None): {
                "timeframe": "3m", "expiry": None}},
            "oracle_assessment_attempts": {},
            "prefs": {"source": "Dhan"},
            "dhan_feed": SimpleNamespace(connected=True),
            "oracle_assessment_context": lambda sym, view: ("3m", None),
            "assessment_lines": lambda sym, cached, **kwargs: (
                [OLD_PLACEHOLDER] if lines is None else lines),
            "regular_hours": lambda: True,
            "watch_three_minute_signal": local_signal,
            "signal_percentages": lambda row: row.get("percentages"),
        }
        exec(compile(module, str(MAIN), "exec"), env)
        result = env["oracle_assessment_notes"]("RELIANCE", surface)
        return result, calls

    def test_unconfigured_oracle_uses_real_historical_three_minute_votes(self):
        result, calls = self._invoke({
            "source": "Dhan", "timeframe": "1m", "historical": True,
            "live_verified": False, "percentages": (33, 67, 8)})
        self.assertEqual(calls, ["RELIANCE"])
        self.assertIn("Dhan phone 1m", result[0])
        self.assertIn("Candle HIST B33/S67", result[0])
        self.assertIn("NOT live", result[0])
        self.assertIn("OI/PCR 4 filters CONTEXT/WAIT", result[0])
        self.assertNotIn("LIVE B33", result[0])

    def test_wrong_frame_or_unverified_source_fails_closed(self):
        for row in (
            {"source": "Dhan", "timeframe": "3m", "historical": True,
             "live_verified": False, "percentages": (33, 67, 8)},
            {"source": "Yahoo Finance", "timeframe": "1m", "historical": True,
             "live_verified": False, "percentages": (33, 67, 8)},
            {"source": "Dhan", "timeframe": "1m", "historical": True,
             "live_verified": True, "percentages": (33, 67, 8)},
        ):
            with self.subTest(row=row):
                result, _ = self._invoke(row)
                self.assertIn("Candle WAIT", result[0])
                self.assertNotIn("B33/S67", result[0])

    def test_scanner_original_oracle_diagnostics_unmodified(self):
        row = {"source": "Dhan", "timeframe": "3m",
               "historical": True, "live_verified": False,
               "percentages": (33, 67, 8)}
        result, calls = self._invoke(row, surface="scanner")
        self.assertEqual(result, [OLD_PLACEHOLDER])
        self.assertFalse(calls)

    def test_already_configured_assessment_not_overridden(self):
        row = {"source": "Dhan", "timeframe": "3m",
               "historical": True, "live_verified": False,
               "percentages": (33, 67, 8)}
        result, calls = self._invoke(row, lines=["Oracle assessment • configured"])
        self.assertEqual(result, ["Oracle assessment • configured"])
        self.assertFalse(calls)

if __name__ == "__main__":
    unittest.main()
