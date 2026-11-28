import sys, unittest
from datetime import datetime, timezone, timedelta
sys.path.insert(0, "src"); sys.path.insert(0, "backend")
import v3_m_forward as m
import clone_signal_runner as rn

IST = timezone(timedelta(hours=5, minutes=30))


def ts(h, mi, day=(2026, 11, 27)):
    return datetime(*day, h, mi, tzinfo=IST).timestamp()


def bars_from(closes, start=(9, 15), rng=1.0):
    out = []
    t0 = ts(*start)
    for i, c in enumerate(closes):
        out.append((t0 + 60 * i, c, c + rng / 2, c - rng / 2, c, 1000))
    return out


class NoiseAndStats(unittest.TestCase):
    def test_noise_move_is_not_scored(self):
        mv = m.min_move(bars_from([100] * 40), 100, 30)
        self.assertGreater(mv, 0.05)
        self.assertIsNone(m.resolve_prediction(100.0, "BULLISH", 100.0 + mv / 2, mv))
        self.assertTrue(m.resolve_prediction(100.0, "BULLISH", 100.0 + mv * 2, mv))
        self.assertFalse(m.resolve_prediction(100.0, "BULLISH", 100.0 - mv * 2, mv))

    def test_wilson_is_more_careful_than_raw_rate(self):
        self.assertLess(m.wilson_low(18, 30), 50)      # 60% on 30 samples is not yet proof
        self.assertGreater(m.wilson_low(21, 30), 50)
        self.assertIsNone(m.wilson_low(0, 0))

    def test_strength_bands(self):
        self.assertEqual([m.strength_band(x) for x in (0.1, 0.4, 0.8)], ["LOW", "MID", "HIGH"])


class Regime(unittest.TestCase):
    def test_sideways_is_damped_and_trend_is_not(self):
        up = bars_from([100 + 0.3 * i for i in range(70)])
        zig = bars_from([100 + (0.4 if i % 2 else -0.4) + 0.02 * i for i in range(70)])
        a = m.m_lean(up, 30); b = m.m_lean(zig, 30)
        self.assertEqual(a["regime"], "TREND")
        self.assertEqual(b["regime"], "SIDEWAYS")
        self.assertLess(b["strength"], a["strength"])

    def test_live_forecast_is_cut_before_close_but_finished_session_keeps_hist(self):
        b = bars_from([100 + 0.3 * i for i in range(70)], start=(14, 0))        # last bar ~15:09
        live_now = b[-1][0] + 60
        self.assertIsNone(m.m_lean(b, 30, now=live_now))                         # live: 15:09 + 30 min > 15:30
        self.assertIsNotNone(m.m_lean(b, 20, now=live_now))                      # 15:09 + 20 = 15:29 is fine
        self.assertIsNotNone(m.m_lean(b, 30, now=live_now + 6 * 3600))           # evening: HIST of the finished session stays
        full = bars_from([100 + 0.2 * i for i in range(375)])                    # whole closed session
        self.assertIsNotNone(m.m_lean(full, 30, now=full[-1][0] + 4 * 3600))


class OrbAndPrevClose(unittest.TestCase):
    def test_orb_break_and_prev_close_checks(self):
        closes = [100] * 15 + [100 + 0.3 * i for i in range(1, 60)]
        b = bars_from(closes, start=(9, 15))
        orb = m.orb_levels(b)
        self.assertGreater(orb["close"], orb["high"])
        lean = {"lean": "BULLISH", "strength": 0.5, "bullish": 70}
        ctx = m.m_context(lean, b, None, b[-1][0], None, prev_close=99.0)
        names = {c["name"]: c["agrees"] for c in ctx["checks"]}
        self.assertTrue(names["ORB"]); self.assertTrue(names["PDC"])
        ctx2 = m.m_context(dict(lean, lean="BEARISH"), b, None, b[-1][0], None, prev_close=99.0)
        self.assertFalse({c["name"]: c["agrees"] for c in ctx2["checks"]}["ORB"])

    def test_no_orb_before_range_is_complete(self):
        self.assertIsNone(m.orb_levels(bars_from([100] * 10)))

    def test_independent_engine_sources_need_two(self):
        b = bars_from([100 + 0.3 * i for i in range(60)])
        lean = {"lean": "BULLISH", "strength": 0.5}
        one = m.m_context(lean, b, ["BULLISH"], b[-1][0])
        two = m.m_context(lean, b, ["BULLISH", "BEARISH"], b[-1][0])
        self.assertNotIn("ENGINES", [c["name"] for c in one["checks"]])
        self.assertFalse({c["name"]: c["agrees"] for c in two["checks"]}["ENGINES"])


class LedgerAndGate(unittest.TestCase):
    def led(self, move):
        led = {}
        out = {"market_open": True, "m_horizons": {"NIFTY": {"30": {"lean": "BULLISH", "ltp": 100.0, "mv": 0.5, "strength": 0.7}}}}
        rn.ledger_step(led, out, 1000)
        out2 = {"market_open": True, "m_lean": {"NIFTY": {"lean": "NEUTRAL", "ltp": 100.0 + move}}}
        rn.ledger_step(led, out2, 1000 + 1800 + 1)
        return led

    def test_noise_sized_row_counts_as_flat_not_scored(self):
        led = self.led(0.2)
        self.assertEqual(led.get("flat"), 1)
        self.assertNotIn("NIFTY@30", led["stats"])

    def test_real_move_scores_with_baseline_and_strength_band(self):
        led = self.led(2.0)
        self.assertEqual(led["stats"]["NIFTY@30"], {"n": 1, "hits": 1, "up": 1})
        self.assertIn("sb:30:HIGH", led["groups"])

    def test_gate_needs_edge_over_market_drift(self):
        # 150 raw 30m samples, 63% hit, but market rose 70% of the time -> always-up would score 70% -> no edge
        led = {"stats": {"NIFTY@30": {"n": 300, "hits": 189, "up": 210}}}
        g = rn.vote_gate(led)
        self.assertEqual(g["M"]["n"], 50)
        self.assertLess(g["M"]["edge"], 0)
        self.assertFalse(g["M"]["eligible"])
        led2 = {"stats": {"NIFTY@30": {"n": 300, "hits": 189, "up": 150}}}   # drift 50% -> edge 13
        g2 = rn.vote_gate(led2)
        self.assertTrue(g2["M"]["eligible"])
        self.assertIn("NIFTY", g2["M_symbols"])

    def test_gate_is_split_per_window(self):
        led = {"stats": {}, "groups": {"w30:BEST_TREND": {"n": 240, "hits": 168}, "w30:MIDDAY_QUIET": {"n": 240, "hits": 110}}}
        g = rn.vote_gate(led)
        self.assertTrue(g["M_windows"]["BEST_TREND"]["eligible"])
        self.assertFalse(g["M_windows"]["MIDDAY_QUIET"]["eligible"])


if __name__ == "__main__":
    unittest.main()


class SharedOverlayMaths(unittest.TestCase):
    def test_supertrend_series_matches_scanner_vote_and_pivot_value(self):
        import scanner_engine as se
        closes=[100+0.5*i for i in range(40)]+[120-0.8*i for i in range(40)]
        b=[(1700000000+60*i,c,c+1,c-1,c,1000) for i,c in enumerate(closes)]
        st=se.supertrend_series(b)
        self.assertEqual(len(st),len(b))
        res=se.analyze([list(x) for x in b],selected=["Supertrend","Pivot Points"],timeframe="1m")
        vote={v["name"]:v["vote"] for v in res["votes"]}
        self.assertEqual(st[-1][1],vote["Supertrend"])
        pv=se.pivot_value(b)
        self.assertEqual(vote["Pivot Points"],1 if closes[-1]>pv else -1 if closes[-1]<pv else 0)

    def test_overlay_is_shared_by_chart_tab_and_home_mini_chart(self):
        src=open("src/main.py",encoding="utf-8").read()
        self.assertIn("def overlay_dots(sym,full_bars,n_vis,y_of,width):",src)
        self.assertEqual(src.count("overlay_dots("),3)   # def + chart tab + mini chart
        self.assertIn('"Supertrend" in fsel',src); self.assertIn('"Pivot Points" in fsel',src)


class IndependentAgreement(unittest.TestCase):
    def test_technical_and_candle_count_as_one_source(self):
        import five_engine as fe
        ev=[fe.EngineEvidence(name=n,bullish=70,bearish=30,timestamp=1.0,source="Dhan",verified=True,reason="x") for n in ("technical","candle","options")]
        ev+=[fe.EngineEvidence(name=n) for n in ("news","futures")]
        ev=sorted(ev,key=lambda e:fe.ENGINE_NAMES.index(e.name))
        r=fe.independent_agreement(ev)
        self.assertEqual((r["raw_count"],r["independent_weight"],r["leader"]),(3,2.0,"BULLISH"))
