import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from v3_m_forward import m_lean, resolve_prediction


def bars(prices, rng=1.0):
    return [(i * 60, p, p + rng / 2, p - rng / 2, p, 100) for i, p in enumerate(prices)]


class MForwardTests(unittest.TestCase):
    def test_thin_data_is_none(self):
        self.assertIsNone(m_lean(bars([100] * 10)))

    def test_uptrend_is_bullish_and_never_a_vote(self):
        r = m_lean(bars([100 + i * 0.5 for i in range(40)]))
        self.assertEqual(r["lean"], "BULLISH"); self.assertGreater(r["bullish"], 55)
        self.assertFalse(r["vote_eligible"]); self.assertEqual(r["bullish"] + r["bearish"], 100)

    def test_downtrend_is_bearish(self):
        self.assertEqual(m_lean(bars([100 - i * 0.5 for i in range(40)]))["lean"], "BEARISH")

    def test_flat_is_neutral(self):
        self.assertEqual(m_lean(bars([100.0] * 40))["lean"], "NEUTRAL")

    def test_bad_rows_are_skipped(self):
        data = bars([100 + i * 0.5 for i in range(40)]) + [("x",), None]
        self.assertIsNotNone(m_lean(data))

    def test_ledger_resolution(self):
        self.assertTrue(resolve_prediction(100, "BULLISH", 101))
        self.assertFalse(resolve_prediction(100, "BULLISH", 99))
        self.assertTrue(resolve_prediction(100, "BEARISH", 99))
        self.assertIsNone(resolve_prediction(100, "NEUTRAL", 105))
        self.assertIsNone(resolve_prediction(100, "BULLISH", 100))


if __name__ == "__main__":
    unittest.main()


class LedgerTests(unittest.TestCase):
    def _runner(self):
        import importlib.util
        root = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(root / "src"))
        spec = importlib.util.spec_from_file_location("runner_b248", root / "backend" / "clone_signal_runner.py")
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        return mod

    def test_record_then_score_after_horizon(self):
        r = self._runner()
        out = {"market_open": True, "m_lean": {"NIFTY": {"lean": "BULLISH", "ltp": 100.0}}}
        led = r.ledger_step({}, out, 1000)
        self.assertEqual(len(led["pending"]), 1)
        led = r.ledger_step(led, dict(out, m_lean={"NIFTY": {"lean": "BULLISH", "ltp": 101.0}}), 1000 + 1200)
        self.assertEqual(led["stats"]["NIFTY"], {"n": 1, "hits": 1})
        self.assertEqual(r.ledger_summary(led)["scored"]["NIFTY"]["hit_rate"], 100.0)

    def test_rate_limited_to_every_five_minutes_and_closed_market_idle(self):
        r = self._runner()
        out = {"market_open": True, "m_lean": {"NIFTY": {"lean": "BEARISH", "ltp": 100.0}}}
        led = r.ledger_step({}, out, 1000)
        led = r.ledger_step(led, out, 1100)
        self.assertEqual(len(led["pending"]), 1)
        self.assertEqual(r.ledger_step({}, dict(out, market_open=False), 1000).get("pending"), [])

    def test_neutral_never_scored(self):
        r = self._runner()
        out = {"market_open": True, "m_lean": {"NIFTY": {"lean": "NEUTRAL", "ltp": 100.0}}}
        led = r.ledger_step({}, out, 1000)
        led = r.ledger_step(led, out, 2300)
        self.assertEqual(led["stats"], {})
