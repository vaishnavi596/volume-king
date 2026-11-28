import sys, unittest, importlib.util, calendar, datetime
sys.path[:0] = ["src", "backend"]
import v3_m_forward as mf, option_ticket as ot, server_paper_positions as sp, clone_signal_runner as rn


def ist(h, m):
    return calendar.timegm(datetime.datetime(2026, 11, 30, h, m).timetuple()) - 19800


def bars(n, up=True, vol_last=200):
    out = []
    for i in range(n):
        c = 100 + (i * 0.1 if up else -i * 0.1)
        out.append((i, c, c + .05, c - .05, c, vol_last if i >= n - 10 else 100))
    return out


class Ctx(unittest.TestCase):
    def test_windows_agree_everywhere(self):
        for h, m in ((9, 20), (9, 50), (10, 30), (11, 45), (12, 30), (14, 0), (15, 10), (8, 0)):
            ts = ist(h, m)
            a, b, c = mf.window_of(ts), ot.time_hint(ts)[0], sp.entry_window(ts)
            self.assertEqual((a, b), (b, c), (h, m))
        self.assertEqual(mf.window_of(ist(10, 30)), "BEST_TREND")

    def test_context_agreement_and_window_dampen(self):
        b = bars(90)
        lean = mf.m_lean(b, 30)
        self.assertEqual(lean["lean"], "BULLISH")
        good = mf.m_context(lean, b, ["BULLISH"] * 4, ist(10, 30))
        self.assertEqual((good["agree"], good["total"]), (3, 3))
        bad = mf.m_context(lean, b, ["BEARISH"] * 4, ist(9, 20))
        self.assertLess(bad["adj_strength"], good["adj_strength"])
        self.assertEqual(mf.m_context(dict(lean, lean="NEUTRAL"), b, [], ist(10, 30)), None)
        self.assertFalse(lean["vote_eligible"])

    def test_ledger_groups(self):
        out = {"market_open": True, "m_lean": {"NIFTY": {"lean": "BULLISH", "ltp": 100.0,
               "context": {"window": "BEST_TREND", "agree": 2, "total": 3}}}}
        led = rn.ledger_step({}, out, 1000)
        out2 = {"market_open": True, "m_lean": {"NIFTY": {"lean": "BULLISH", "ltp": 101.0}}}
        led = rn.ledger_step(led, out2, 1000 + 1300)
        s = rn.ledger_summary(led)
        self.assertEqual(s["groups"]["w:BEST_TREND"]["hit_rate"], 100.0)
        self.assertIn("c:2/3", s["groups"])


class WindowStats(unittest.TestCase):
    def test_engine_window_stats(self):
        t = [ist(10, 30)]
        e = sp.PaperEngine(None, clock=lambda: t[0])
        e.open_option("X", {"seg": "NSE_FNO", "sid": 1}, 65, 1, 100, 50, 120, expires_at=9e9)
        self.assertEqual(e.open_positions()[0]["window"], "BEST_TREND")
        e.observe({"X": 121})
        self.assertEqual(e.window_stats()["BEST_TREND"]["target"], 1)
        self.assertIn("window_stats", e.state())


if __name__ == "__main__":
    unittest.main()
