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
