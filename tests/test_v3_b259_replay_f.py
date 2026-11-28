import sys, unittest
sys.path[:0] = ["src", "backend"]


def day_bars(day_ts, n=200, start=100.0, step=0.1):
    return [[day_ts + 60 * i, start + step * i, start + step * i + 0.05, start + step * i - 0.05, start + step * i, 1000] for i in range(n)]


class FutReplay(unittest.TestCase):
    def test_split_fut_keeps_oi_aligned(self):
        import clone_replay as c
        base = 1_700_000_000
        bars = day_bars(base)
        oi = [1000.0 + i for i in range(len(bars))]
        days = c.split_fut(bars, oi)
        self.assertEqual(len(days), 1)
        b, o = next(iter(days.values()))
        self.assertEqual(len(b), len(o))
        self.assertIsNone(next(iter(c.split_fut(bars, None).values()))[1])

    def test_fut_bias_uses_only_past_candles(self):
        import clone_replay as c
        base = 1_700_000_000
        bars = day_bars(base, 200, 100.0, 0.1)
        fut = (bars, None)
        self.assertIsNone(c.fut_bias(fut, bars[10][0]))            # too little history
        late = c.fut_bias(fut, bars[120][0])
        self.assertIn(late, ("BULLISH", None))                     # a steady rise never reads bearish
        self.assertIsNone(c.fut_bias(None, bars[120][0]))

    def test_gate_prefers_replay_for_f(self):
        import clone_signal_runner as r
        replay = {"box_hit": {"F": {"30m": {"n": 300, "hit_rate": 58.0, "up_rate": 50.0}}}}
        g = r.vote_gate({"stats": {}}, replay)
        self.assertGreater(g["F"]["n"], 0)
        self.assertEqual(g["F"]["horizon"], "30m")


if __name__ == "__main__":
    unittest.main()
