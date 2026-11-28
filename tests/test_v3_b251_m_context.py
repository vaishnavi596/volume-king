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


class OiMorning(unittest.TestCase):
    def test_oi_check_in_context(self):
        b = bars(90)
        lean = mf.m_lean(b, 30)
        c = mf.m_context(lean, b, None, ist(10, 30), {"bullish": 70, "bearish": 30})
        self.assertIn("OI", [x["name"] for x in c["checks"]])
        self.assertTrue([x for x in c["checks"] if x["name"] == "OI"][0]["agrees"])
        c2 = mf.m_context(lean, b, None, ist(10, 30), {"bullish": 30, "bearish": 70})
        self.assertFalse([x for x in c2["checks"] if x["name"] == "OI"][0]["agrees"])
        c3 = mf.m_context(lean, b, None, ist(10, 30), {"bullish": 52, "bearish": 48})
        self.assertNotIn("OI", [x["name"] for x in c3["checks"]])

    def test_morning_ledger_scores_close(self):
        out = {"oi_lean": {"NIFTY": {"bullish": 70}}, "spot": {"NIFTY": 100.0}}
        led = rn.oi_morning_step({}, out, ist(9, 30))
        self.assertIn("NIFTY", list(led["oi_morning"].values())[0])
        led = rn.oi_morning_step(led, {"oi_lean": {}, "spot": {"NIFTY": 101.0}}, ist(15, 25))
        s = rn.ledger_summary(led)
        self.assertEqual(s["oi_morning"]["NIFTY"], {"n": 1, "hit_rate": 100.0})
        # weak lean is recorded but not scored
        led2 = rn.oi_morning_step({}, {"oi_lean": {"BANKNIFTY": {"bullish": 54}}, "spot": {"BANKNIFTY": 100.0}}, ist(9, 30))
        led2 = rn.oi_morning_step(led2, {"spot": {"BANKNIFTY": 99.0}}, ist(15, 25))
        self.assertEqual(rn.ledger_summary(led2)["oi_morning"], {})

    def test_oi_snapshot_uses_gateway_and_never_orders(self):
        calls = []
        def fake_post(path, body, key, timeout=25):
            calls.append(path)
            if path.endswith("expiries"):
                return {"expiries": ["2026-11-24", "2026-12-01"]}
            rows = [{"strike": 100 + i, "ce": {"oi": 10, "previous_oi": 10, "last_price": 5.0},
                     "pe": {"oi": 20 if i == 3 else 10, "previous_oi": 10, "last_price": 5.0}} for i in range(7)]
            return {"pcr": 1.1, "max_pain": 103, "atm_window": {"source": "dhan", "atm": 103, "rows": rows}}
        orig = rn.post
        rn.post = fake_post
        try:
            row = rn.oi_snapshot("k", "NIFTY", "2026-11-30", {})
        finally:
            rn.post = orig
        self.assertEqual(row["expiry"], "2026-12-01")
        self.assertGreater(row["bullish"], 50)
        self.assertTrue(all("/market/" in c for c in calls))


class NewsCue(unittest.TestCase):
    RSS = (b'<rss><channel>' + b''.join(
        b'<item><title>' + t + b'</title><link>https://x/' + str(i).encode() + b'</link><pubDate>Mon, 30 Nov 2026 04:00:00 GMT</pubDate></item>'
        for i, t in enumerate([b"Nifty rallies on strong flows", b"Sensex surges to record high", b"Bank stocks tumble in sell-off", b"Nifty may rise tomorrow"]))
        + b'</channel></rss>')

    def test_parse_and_cue(self):
        import v3_news_cue as nc
        now = calendar.timegm(datetime.datetime(2026, 11, 30, 6, 0).timetuple())
        items = nc.parse_news_rss(self.RSS, "t", now)
        self.assertEqual(len(items), 4)
        sig = nc.headline_signal(items)
        self.assertEqual((sig["positive"], sig["negative"]), (2, 1))      # "may" headline skipped
        self.assertEqual(sig["bullish"], 67)
        with self.assertRaises(ValueError):
            nc.parse_news_rss(b"<!DOCTYPE x><rss/>", "t", now)

    def test_runner_refresh_is_bounded_and_carries(self):
        import io
        class R:
            def __init__(s, b): s.b = b
            def read(s, n): return s.b[:n]
            def __enter__(s): return s
            def __exit__(s, *a): return False
        class O:
            def open(s, req, timeout=0): return R(NewsCue.RSS)
        now = calendar.timegm(datetime.datetime(2026, 11, 30, 6, 0).timetuple())
        rn.NEWS_STATE.update(at=0.0, cue={})
        cue = rn.news_refresh(now, O())
        self.assertEqual(sorted(cue), ["BANKNIFTY", "NIFTY", "SENSEX"])
        again = rn.news_refresh(now + 60, O())      # inside 10 min: no new fetch, same cue
        self.assertIs(again, rn.NEWS_STATE["cue"])

    def test_news_morning_ledger(self):
        led = rn.oi_morning_step({}, {"news_cue": {"NIFTY": {"bullish": 67}}, "spot": {"NIFTY": 100.0}}, ist(9, 40), "news_cue", "news_morning", "news_stats")
        led = rn.oi_morning_step(led, {"spot": {"NIFTY": 99.0}}, ist(15, 25), "news_cue", "news_morning", "news_stats")
        self.assertEqual(rn.ledger_summary(led)["news_morning"]["NIFTY"], {"n": 1, "hit_rate": 0.0})


class FuturesLean(unittest.TestCase):
    MASTER = ("SEM_INSTRUMENT_NAME,SEM_TRADING_SYMBOL,SEM_EXM_EXCH_ID,SEM_EXPIRY_DATE,SEM_SMST_SECURITY_ID,SEM_LOT_UNITS\n"
              "FUTIDX,NIFTY-Dec2026-FUT,NSE,2026-12-29 14:30:00,111,65\n"
              "FUTIDX,NIFTY-Jan2027-FUT,NSE,2027-01-26 14:30:00,112,65\n"
              "FUTIDX,SENSEX-Dec2026-FUT,BSE,2026-12-29 14:30:00,222,20\n"
              "FUTIDX,NIFTY-Nov2026-FUT,NSE,2026-11-24 14:30:00,100,65\n"
              "OPTIDX,NIFTY-Dec2026-24500-CE,NSE,2026-12-29,5,65\n")

    def test_parse_nearest_future(self):
        import io
        f = rn.parse_future_contracts(io.StringIO(self.MASTER), "2026-11-30")
        self.assertEqual(f["NIFTY"], ["NSE_FNO", 111, 65, "2026-12-29"])
        self.assertEqual(f["SENSEX"][0], "BSE_FNO")
        self.assertNotIn("BANKNIFTY", f)

    def test_snapshot_lean_and_premium(self):
        idx = [(60 * i, 100, 100.1, 99.9, 100 + i * 0.1, 10) for i in range(90)]
        fut = [[60 * i, 101, 101.1, 100.9, 101 + i * 0.1 + (i * 0.02), 10] for i in range(90)]
        orig = rn.post
        rn.post = lambda path, body, key, timeout=25: {"bars": fut}
        try:
            snap = rn.fut_snapshot("k", "NIFTY", "2026-11-30", {"NIFTY": ["NSE_FNO", 1, 65, "2026-12-29"]}, idx)
            none = rn.fut_snapshot("k", "BANKNIFTY", "2026-11-30", {}, idx)
        finally:
            rn.post = orig
        self.assertIsNone(none)
        self.assertGreater(snap["bullish"], 50)
        self.assertTrue(snap["basis_agrees"])
        self.assertGreater(snap["basis_change_30m"], 0)

    def test_gateway_route_is_read_only_and_wired(self):
        src = open("backend/clone_v2_gateway.py", encoding="utf-8").read()
        a = src.index('"/clone-v2/market/futures/candles"')
        body = src[a:a + 3500]
        self.assertIn("authorized(x_botking_key)", body)
        self.assertIn('"instrument": "FUTIDX"', body)
        self.assertNotIn("order", body.lower().replace("orders", "").replace("live_orders_enabled", ""))


class VoteGate(unittest.TestCase):
    def test_gate_needs_samples_and_rate(self):
        led = {"stats": {"NIFTY@30": {"n": 20, "hits": 13}}, "oi_stats": {"NIFTY": {"n": 40, "hits": 24}},
               "news_stats": {"NIFTY": {"n": 40, "hits": 18}}, "fut_stats": {}}
        g = rn.vote_gate(led)
        self.assertFalse(g["M"]["eligible"])                 # n=20 < 30
        self.assertTrue(g["O"]["eligible"])                  # 40 samples, 60%
        self.assertFalse(g["N"]["eligible"])                 # 45% < 55%
        self.assertFalse(g["F"]["eligible"]); self.assertIsNone(g["F"]["hit_rate"])
        rep = {"m_hit": {"30m": {"n": 600, "hit_rate": 60.0}}}   # 600/6 = 100 effective samples
        g2 = rn.vote_gate(led, rep)
        self.assertTrue(g2["M"]["eligible"])
        self.assertEqual(g2["M"]["n"], 120)


class GatedFuturesVote(unittest.TestCase):
    def comp(self, **kw):
        base = {"source": "Dhan", "verified": True, "direction_basis": "ledger_gated_lean", "symbol": "NIFTY",
                "underlying": "NIFTY", "timeframe": "1m", "generation": 3, "expiry": "2026-12-29",
                "contract": "NIFTY FUT 2026-12-29", "bullish": 62, "bearish": 38, "timestamp": 1000.0,
                "mapping_verified": True, "live_verified": True, "historical": False}
        base.update(kw)
        return base

    def test_adapter_accepts_gated_basis_only(self):
        import five_engine as fe
        ok = fe.futures_from_component(self.comp())
        self.assertTrue(ok.eligible); self.assertEqual((ok.bullish, ok.bearish), (62, 38))
        self.assertFalse(fe.futures_from_component(self.comp(direction_basis="inferred_buildup")).eligible)
        self.assertFalse(fe.futures_from_component(self.comp(historical=True)).eligible)

    def test_publish_freshness_window(self):
        import five_engine as fe
        eng = fe.compose_snapshot()
        self.assertEqual(fe.LEDGER_GATED_MAX_AGE_SECONDS, 290)
        src = open("src/five_engine.py", encoding="utf-8").read()
        self.assertIn('LEDGER_GATED_MAX_AGE_SECONDS if component.get("direction_basis")=="ledger_gated_lean" else 90', src)

    def test_phone_builds_gated_component_only_when_eligible(self):
        src = open("src/main.py", encoding="utf-8").read()
        self.assertIn('_gate.get("eligible") is True', src)
        self.assertIn('"direction_basis":"ledger_gated_lean"', src)
