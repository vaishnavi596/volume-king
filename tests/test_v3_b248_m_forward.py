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
        self.assertEqual(led["stats"]["NIFTY"], {"n": 1, "hits": 1, "up": 1})
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


class Horizons(unittest.TestCase):
    def _bars(self, n, step):
        return [(i, 100 + i * step, 100.5 + i * step, 99.5 + i * step, 100 + i * step, 1) for i in range(n)]
    def test_horizons_and_min_bars(self):
        import v3_m_forward as m
        self.assertIsNone(m.m_lean(self._bars(40, 0.2), 60))
        self.assertEqual(m.m_lean(self._bars(80, 0.2), 60)["horizon_minutes"], 60)
        self.assertEqual(m.m_lean(self._bars(40, 0.2), 30)["lean"], "BULLISH")
        self.assertIsNone(m.m_lean(self._bars(80, 0.2), 45))
        self.assertEqual(set(m.m_leans(self._bars(80, -0.2))), {"20", "30", "60"})
    def test_confidence_label(self):
        import v3_m_forward as m
        self.assertEqual(m.confidence_label(0.7), "मज़बूत")
        self.assertEqual(m.confidence_label(0.1), "हल्का")
    def test_ledger_scores_30_minute_rows(self):
        import clone_signal_runner as r
        led = {}
        out = {"market_open": True, "m_lean": {"NIFTY": {"lean": "BULLISH", "ltp": 100.0}},
               "m_horizons": {"NIFTY": {"30": {"lean": "BULLISH", "ltp": 100.0}}}}
        r.ledger_step(led, out, 1000)
        out2 = {"market_open": True, "m_lean": {"NIFTY": {"lean": "BULLISH", "ltp": 101.0}}}
        r.ledger_step(led, out2, 1000 + 31 * 60)
        self.assertEqual(led["stats"]["NIFTY@30"], {"n": 1, "hits": 1, "up": 1})


class LotSizes(unittest.TestCase):
    def test_parse(self):
        import clone_signal_runner as r
        lines = ["SEM_INSTRUMENT_NAME,SEM_TRADING_SYMBOL,SEM_LOT_UNITS",
                 "OPTIDX,NIFTY-Dec2026-20000-CE,65.0", "OPTIDX,NIFTY-Dec2026-20050-CE,99.0",
                 "OPTIDX,BANKNIFTY-Dec2026-69400-CE,30.0", "OPTSTK,RELIANCE-Dec2026-1500-CE,500.0",
                 "FUTCUR,USDINR-28Aug2024-FUT,1.0", "OPTIDX,BAD-X,abc"]
        self.assertEqual(r.parse_lot_sizes(lines), {"NIFTY": 65, "BANKNIFTY": 30, "RELIANCE": 500})
