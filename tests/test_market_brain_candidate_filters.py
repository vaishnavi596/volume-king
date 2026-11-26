import unittest

from market_brain import candidate_filters as cf

IST = 19800


def mk(day, closes, start_min=9 * 60 + 15, spread=1.0):
    base = day * 86400 - IST + start_min * 60
    return [(base + i * 300, c, c + spread, c - spread, c, 0.0) for i, c in enumerate(closes)]


class CandidateFilterTests(unittest.TestCase):
    def test_orb_breakout_up_down_and_inside(self):
        flat = [100.0] * 6
        self.assertEqual(cf.orb(mk(20000, flat + [105.0])), 1)
        self.assertEqual(cf.orb(mk(20000, flat + [95.0])), -1)
        self.assertEqual(cf.orb(mk(20000, flat + [100.5])), 0)
        self.assertEqual(cf.orb(mk(20000, flat[:5])), 0)       # range not complete yet

    def test_orb_ignores_bars_after_the_last_one(self):
        base = mk(20000, [100.0] * 6 + [100.2])
        longer = mk(20000, [100.0] * 6 + [100.2, 130.0])
        self.assertEqual(cf.orb(base), 0)
        self.assertEqual(cf.orb(longer[:-1]), 0)               # future bar must not leak

    def test_prev_day_levels(self):
        prev = mk(20000, [100.0, 101.0, 99.0, 100.0])
        up = mk(20001, [102.0] + [103.0])
        dn = mk(20001, [97.0] + [96.0])
        mid = mk(20001, [100.0] + [100.0])
        self.assertEqual(cf.prev_day_levels(prev + up), 1)
        self.assertEqual(cf.prev_day_levels(prev + dn), -1)
        self.assertEqual(cf.prev_day_levels(prev + mid), 0)
        self.assertEqual(cf.prev_day_levels(up), 0)            # no previous day -> abstain
        self.assertEqual(cf.prev_day_close_bias(prev + up), 1)

    def test_adx_trend_direction_and_flat(self):
        up = mk(20000, [100 + i * 0.8 for i in range(80)])
        dn = mk(20000, [200 - i * 0.8 for i in range(80)])
        flat = mk(20000, [100.0 + (0.1 if i % 2 else -0.1) for i in range(80)])
        self.assertEqual(cf.adx_trend(up), 1)
        self.assertEqual(cf.adx_trend(dn), -1)
        self.assertEqual(cf.adx_trend(flat), 0)
        self.assertEqual(cf.adx_trend(up[:20]), 0)


if __name__ == "__main__":
    unittest.main()
