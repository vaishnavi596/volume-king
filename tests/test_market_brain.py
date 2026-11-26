import math
import random
import unittest

try:
    import numpy  # noqa: F401
except ImportError:  # CI image has no numpy; Market Brain is a standalone server component
    raise unittest.SkipTest("numpy not installed")

from market_brain.backtest import scorecard, walk_forward
from market_brain.features import IST, build_samples, day_key
from market_brain.memory import BrainMemory


def synth(days=140, seed=1, reversion=0.0, tod=0.0):
    """5m bars 09:15-15:30 IST. reversion pulls price back toward the 20-day mean at the
    close of each 30 min; tod adds a fixed up-drift after 13:15."""
    rnd = random.Random(seed)
    bars, price, base_day = [], 100.0, 20000
    hist = [price]
    for d in range(days):
        day0 = (base_day + d) * 86400 - IST
        mean20 = sum(hist[-20:]) / len(hist[-20:])
        for i in range(75):
            ts = day0 + (9 * 60 + 15 + 5 * i) * 60
            drift = reversion * (mean20 - price) / price
            if tod and (9 * 60 + 15 + 5 * i) >= 13 * 60 + 15:
                drift += tod
            o = price
            price = max(1.0, price * (1 + drift + rnd.gauss(0, 0.0012)))
            bars.append((ts, o, max(o, price) * 1.0002, min(o, price) * 0.9998, price, 1000))
        hist.append(price)
    return bars


class BrainTests(unittest.TestCase):
    def test_no_lookahead_features_unchanged_by_future_bars(self):
        bars = synth(days=40, seed=3)
        a = build_samples(bars)
        cut = 30 * 75 * 5 // 5
        altered = bars[:cut] + [(t, o * 1.5, h * 1.5, l * 1.5, c * 1.5, v) for t, o, h, l, c, v in bars[cut:]]
        b = build_samples(altered)
        early = [s for s in a if s["ts"] < bars[cut][0] - 3600]
        early_b = [s for s in b if s["ts"] < bars[cut][0] - 3600]
        self.assertGreater(len(early), 20)
        self.assertEqual([s["x"] for s in early], [s["x"] for s in early_b])

    def test_random_walk_shows_no_fake_skill(self):
        bars = synth(days=200, seed=5)
        s = build_samples(bars)
        days = sorted({x["day"] for x in s})
        rows = walk_forward(s, days[-60:], min_train=200)
        card = scorecard(rows)
        self.assertGreater(card["n"], 200)
        self.assertLess(card["skill_vs_best_baseline"] or 0, 0.05)

    def test_planted_time_of_day_effect_is_found(self):
        bars = synth(days=200, seed=7, tod=0.0004)
        s = build_samples(bars)
        days = sorted({x["day"] for x in s})
        card = scorecard(walk_forward(s, days[-60:], min_train=200))
        late = [v for k, v in card["by_time"].items() if k >= "13:45"]
        self.assertTrue(late)
        self.assertGreater(sum(a * n for a, n in late) / sum(n for _, n in late), 0.55)

    def test_training_only_uses_earlier_days(self):
        s = build_samples(synth(days=120, seed=9))
        days = sorted({x["day"] for x in s})
        rows = walk_forward(s, days[-20:], min_train=100)
        self.assertTrue(rows)
        for r in rows:
            self.assertLess(r["trained_through"], r["day"] + 1)
            self.assertLessEqual(r["trained_through"], r["day"])

    def test_memory_is_append_only_and_idempotent(self):
        m = BrainMemory()
        self.assertTrue(m.add_prediction("p1", "RELIANCE", 1000.0, 30, "BULLISH", 0.6, "v1", {"k": 1}))
        self.assertFalse(m.add_prediction("p1", "RELIANCE", 1000.0, 30, "BEARISH", 0.4, "v1", {}))
        with self.assertRaises(Exception):
            m.db.execute("UPDATE prediction_event SET call='X'")
        with self.assertRaises(Exception):
            m.db.execute("DELETE FROM prediction_event")
        m.add_outcome("o1", "p1", 2800.0, 0.002, True)
        self.assertEqual(m.own_record("RELIANCE", 0)["n"], 1)


if __name__ == "__main__":
    unittest.main()
