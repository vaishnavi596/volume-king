import random
import unittest

try:
    import numpy  # noqa: F401
except ImportError:  # CI image has no numpy; Market Brain is a standalone server component
    raise unittest.SkipTest("numpy not installed")

from market_brain import volatility as vol

IST = 19800


def day_bars(day, scale, rnd, n=75):
    base = day * 86400 - IST + (9 * 60 + 15) * 60
    p, rows = 20000.0, []
    for i in range(n):
        o = p
        c = o * (1 + rnd.gauss(0, 0.0005 * scale))
        h, l = max(o, c) * 1.0001, min(o, c) * 0.9999
        rows.append((base + i * 300, o, h, l, c, 0.0))
        p = c
    return rows


class VolatilityTests(unittest.TestCase):
    def make(self, regimes):
        rnd = random.Random(3)
        return {20000 + i: day_bars(20000 + i, s, rnd) for i, s in enumerate(regimes)}

    def test_clustered_volatility_is_predicted(self):
        reg = ([1] * 15 + [4] * 15) * 8
        rows = vol.build_days(self.make(reg))
        hit = n = 0
        for j in range(100, len(rows)):
            p = vol.predict_today(rows[:j], rows[j]["x"])
            hit += (p > 0.5) == bool(rows[j]["big"]); n += 1
        self.assertGreater(hit / n, 0.7)

    def test_no_future_label_used(self):
        rows = vol.build_days(self.make([1, 2] * 60))
        a = vol.predict_today(rows[:80], rows[80]["x"])
        rows2 = [dict(r) for r in rows]
        for r in rows2[80:]:
            r["big"] = 1 - r["big"]
        self.assertEqual(a, vol.predict_today(rows2[:80], rows2[80]["x"]))

    def test_too_little_data_abstains(self):
        rows = vol.build_days(self.make([1] * 40))
        self.assertIsNone(vol.predict_today(rows[:5], rows[5]["x"]))
        self.assertEqual(vol.verdict(None), "डेटा नाकाफ़ी")

    def test_verdict_bands(self):
        self.assertIn("बड़ी", vol.verdict(0.7)); self.assertIn("शांत", vol.verdict(0.3))
        self.assertIn("साफ़ संकेत नहीं", vol.verdict(0.5))


if __name__ == "__main__":
    unittest.main()
