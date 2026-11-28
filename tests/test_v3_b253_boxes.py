import sys, unittest
sys.path.insert(0, "src"); sys.path.insert(0, "backend")
import v3_fut_buildup as fb
import v3_heavyweights as hw
import clone_signal_runner as rn
import clone_replay as rp


def bars(closes, rng=1.0):
    return [(1700000000 + 60 * i, c, c + rng / 2, c - rng / 2, c, 1000) for i, c in enumerate(closes)]


class Buildup(unittest.TestCase):
    def test_four_states(self):
        up = bars([100 + 0.1 * i for i in range(40)]); dn = bars([100 - 0.1 * i for i in range(40)])
        oi_up = [1000 + 10 * i for i in range(40)]; oi_dn = [1000 - 10 * i for i in range(40)]
        self.assertEqual(fb.futures_buildup(up, oi_up)["state"], "LONG_BUILDUP")
        self.assertEqual(fb.futures_buildup(dn, oi_up)["state"], "SHORT_BUILDUP")
        self.assertEqual(fb.futures_buildup(up, oi_dn)["state"], "SHORT_COVERING")
        self.assertEqual(fb.futures_buildup(dn, oi_dn)["state"], "LONG_UNWINDING")
        self.assertEqual(fb.futures_buildup(up, oi_up)["direction"], "BULLISH")

    def test_missing_or_flat_oi_gives_nothing(self):
        up = bars([100 + 0.1 * i for i in range(40)])
        self.assertIsNone(fb.futures_buildup(up, None))
        self.assertIsNone(fb.futures_buildup(up, [1000] * 40))
        self.assertIsNone(fb.futures_buildup(up, [1000] * 39))
        self.assertIsNone(fb.futures_buildup(bars([100] * 40), [1000 + i * 10 for i in range(40)]))

    def test_gateway_asks_for_oi_with_plain_fallback_and_stays_read_only(self):
        src = open("backend/clone_v2_gateway.py", encoding="utf-8").read()
        a = src.index('"/clone-v2/market/futures/candles"')
        body = src[a:a + 5200]
        self.assertIn("dict(args, oi=True)", body); self.assertIn('"oi": oi_series', body)
        self.assertNotIn("order", body.lower().replace("orders", "").replace("live_orders_enabled", ""))

    def test_runner_applies_buildup_to_futures_lean(self):
        src = open("backend/clone_signal_runner.py", encoding="utf-8").read()
        self.assertIn("futures_buildup(bars, resp.get(\"oi\"))", src)
        self.assertIn('"buildup"', src)


class Heavy(unittest.TestCase):
    def test_weighted_lean_and_coverage(self):
        up = bars([100 + 0.5 * i for i in range(45)]); dn = bars([100 - 0.5 * i for i in range(45)])
        r = hw.heavy_lean("NIFTY", {"HDFCBANK": up, "RELIANCE": up, "ICICIBANK": up, "INFY": dn, "TCS": dn})
        self.assertEqual(r["lean"], "BULLISH"); self.assertEqual(r["coverage"], 1.0)
        r2 = hw.heavy_lean("NIFTY", {"HDFCBANK": dn, "RELIANCE": dn, "ICICIBANK": dn, "INFY": up, "TCS": up})
        self.assertEqual(r2["lean"], "BEARISH")
        self.assertIsNone(hw.heavy_lean("NIFTY", {"TCS": up}))            # coverage too thin
        self.assertIsNone(hw.heavy_lean("NIFTY", {k: bars([100] * 45) for k in hw.WEIGHTS["NIFTY"]}))   # nobody decisive
        self.assertFalse(r["vote_eligible"])


class ReplayAndGate(unittest.TestCase):
    def test_body_balance(self):
        up = [(i, 100 + i, 102 + i, 99 + i, 101.5 + i, 1) for i in range(10)]
        dn = [(i, 100 - i, 101 - i, 98 - i, 99 - i, 1) for i in range(10)]
        self.assertEqual(rp.body_balance(up), "BULLISH"); self.assertEqual(rp.body_balance(dn), "BEARISH")

    def test_replay_day_fills_box_hits_with_baseline(self):
        closes = [100 + 0.2 * i for i in range(220)]
        report = {"horizons": {}, "windows": {}, "confluence": {}, "engine_dir": {}, "box": {},
                  "engine": {"calls": 0, "errors": 0, "directional_ge3": 0}, "days": [], "symbols": {}}
        b = [(1700000000 + 60 * i, c - 0.1, c + 0.5, c - 0.5, c, 1000) for i, c in enumerate(closes)]
        rp.replay_day(b, report)
        self.assertIn("C", report["box"])
        fin = rp.finish(report["box"]["C"])
        self.assertIn("30m", fin); self.assertIsNotNone(fin["30m"]["up_rate"])

    def test_gate_rows_for_t_c_h_from_replay_and_morning_split(self):
        rep = {"box_hit": {"T": {"30m": {"n": 600, "hit_rate": 62.0, "up_rate": 50.0}},
                           "C": {"30m": {"n": 600, "hit_rate": 51.0, "up_rate": 50.0}}}}
        g = rn.vote_gate({"heavy_stats": {"NIFTY": {"n": 4, "hits": 3}}}, rep)
        self.assertEqual(g["T"]["n"], 100); self.assertTrue(g["T"]["eligible"])
        self.assertFalse(g["C"]["eligible"])                   # 51% is not above the bar
        self.assertEqual(g["H"]["n"], 0); self.assertFalse(g["H"]["eligible"])
        self.assertEqual(g["H_morning"]["n"], 4)

    def test_installer_ships_new_modules_and_replay_has_room(self):
        inst = open("ops/install_server_away_20261127.sh", encoding="utf-8").read()
        self.assertEqual(inst.count("v3_fut_buildup.py v3_heavyweights.py"), 3)
        self.assertIn("timeout 900", open("ops/botking_autoupdate.sh", encoding="utf-8").read())


if __name__ == "__main__":
    unittest.main()


class SignalSizeGuard(unittest.TestCase):
    def test_signal_file_is_capped_below_gateway_limit(self):
        import json
        big = {"market_open": True, "symbols": {}, "replay": {"x": "y" * 70000}, "m_ledger": {"a": 1}}
        text = rn.cap_signal_size(big)
        self.assertLess(len(text.encode()), 60000)
        d = json.loads(text)
        self.assertIn("replay", d["trimmed"]); self.assertIn("m_ledger", d)
        small = rn.cap_signal_size({"a": 1})
        self.assertNotIn("trimmed", json.loads(small))
