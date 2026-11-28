import sys, tempfile, os, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from server_paper_positions import PaperEngine, LIVE_ORDERS_ENABLED


class PaperEngineTests(unittest.TestCase):
    def test_live_is_off_and_state_says_paper(self):
        e = PaperEngine()
        self.assertFalse(LIVE_ORDERS_ENABLED)
        hb = e.heartbeat()
        self.assertEqual(hb["mode"], "PAPER")
        self.assertFalse(hb["live_orders_enabled"])

    def test_stop_loss_closes_buy_and_pnl(self):
        e = PaperEngine()
        p = e.open("TCS", "BUY", 10, 100.0, 95.0, 110.0)
        self.assertEqual(e.observe({"TCS": 99}), [])
        closed = e.observe({"TCS": 94})
        self.assertEqual(closed[0]["reason"], "STOP_LOSS")
        self.assertEqual(closed[0]["pnl"], -50.0)
        self.assertEqual(e.heartbeat()["open_count"], 0)

    def test_target_and_sell_side(self):
        e = PaperEngine()
        e.open("INFY", "SELL", 5, 100.0, 105.0, 90.0)
        self.assertEqual(e.observe({"INFY": 89})[0]["reason"], "TARGET")
        self.assertEqual(e.positions[0]["pnl"], 50.0)

    def test_rejects_missing_or_wrong_side_stop(self):
        e = PaperEngine()
        with self.assertRaises(ValueError): e.open("TCS", "BUY", 1, 100, 101)
        with self.assertRaises(ValueError): e.open("TCS", "SELL", 1, 100, 99)
        with self.assertRaises(ValueError): e.open("TCS", "BUY", 1, 100, None)
        with self.assertRaises(ValueError): e.open("TCS", "HOLD", 1, 100, 90)
        with self.assertRaises(ValueError): e.open("TCS", "BUY", 0, 100, 90)

    def test_persistence_survives_restart(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "paper.json")
            PaperEngine(path).open("TCS", "BUY", 1, 100, 90)
            self.assertEqual(PaperEngine(path).heartbeat()["open_count"], 1)

    def test_manual_close_needs_price(self):
        e = PaperEngine()
        p = e.open("TCS", "BUY", 1, 100, 90)
        with self.assertRaises(ValueError): e.close(p["id"])
        self.assertEqual(e.close(p["id"], 103)["pnl"], 3.0)

    def test_max_open_limit(self):
        e = PaperEngine()
        for i in range(10): e.open("S%d" % i, "BUY", 1, 100, 90)
        with self.assertRaises(ValueError): e.open("X", "BUY", 1, 100, 90)

    def test_gateway_routes_are_paper_only_and_authorized(self):
        src = (Path(__file__).resolve().parents[1] / "backend" / "clone_v2_gateway.py").read_text()
        for r in ("paper/heartbeat", "paper/state", "paper/open", "paper/close"):
            self.assertIn('"/clone-v2/' + r + '"', src)
        seg = src[src.index("B244: server-side PAPER"):]
        self.assertEqual(seg.count("authorized(x_botking_key)"), 10)  # B249/B250: + open-option, preview-option; B255: + edit; B261: + snapshot/boxes
        for banned in ("place_order", "/orders", "super_order", "/v2/orders"):
            self.assertNotIn(banned, seg)


if __name__ == "__main__":
    unittest.main()


class PhoneHeartbeatClientTests(unittest.TestCase):
    def _gw(self, payload, url="https://x.example/clone-v2/paper/heartbeat"):
        import io, json as _j
        import importlib.util
        spec = importlib.util.spec_from_file_location("phone_clone_gw", Path(__file__).resolve().parents[1] / "src" / "clone_v2_gateway.py")
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        CloneV2Gateway = mod.CloneV2Gateway

        class Resp:
            status = 200
            def __init__(s): s.headers = type("H", (), {"get_content_type": lambda self: "application/json"})(); s.b = io.BytesIO(_j.dumps(payload).encode())
            def geturl(s): return url
            def read(s, n): return s.b.read(n)
            def __enter__(s): return s
            def __exit__(s, *a): return False
        class Op:
            def open(self, req, timeout=0): return Resp()
        g = CloneV2Gateway(opener=Op()); g._origin = "https://x.example"; g._key = "k" * 40
        return g

    def test_valid_heartbeat(self):
        r = self._gw({"mode": "PAPER", "live_orders_enabled": False, "open_count": 2, "uptime_seconds": 5}).paper_heartbeat()
        self.assertTrue(r["reachable"]); self.assertEqual(r["open_count"], 2); self.assertFalse(r["live_orders_enabled"])

    def test_live_true_is_rejected(self):
        r = self._gw({"mode": "PAPER", "live_orders_enabled": True}).paper_heartbeat()
        self.assertFalse(r["reachable"])

    def test_disconnected(self):
        self.assertFalse(self._gw({}).__class__().paper_heartbeat()["reachable"])


class B245AppWiringTests(unittest.TestCase):
    def test_server_paper_ui_is_paper_only_and_wired(self):
        src = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text()
        for needle in ("def server_paper_section(show_controls=True):", "async def paper_server_open(side):",
                       "async def paper_server_close(pos_id):", "server_paper_section(),",
                       "page.run_task(paper_heartbeat_poll)", "no real order"):
            self.assertIn(needle, src)
        gw = (Path(__file__).resolve().parents[1] / "src" / "clone_v2_gateway.py").read_text()
        self.assertIn('"signals/latest","signals/journal"', gw)
        self.assertIn('out.get("live_orders_enabled") is not False', gw)

    def test_doctor_o_box_reports_oi_change_hist(self):
        src = (Path(__file__).resolve().parents[1] / "src" / "v3_four_box_source_readiness.py").read_text()
        self.assertIn('sources["O"]["oi_change_hist"]', src)
        self.assertIn("display_only", src)


class B246ServerAwayTests(unittest.TestCase):
    def test_change_events_and_journal_trim(self):
        import importlib.util, tempfile
        root = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(root / "src"))
        spec = importlib.util.spec_from_file_location("signal_runner_b246", root / "backend" / "clone_signal_runner.py")
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        prev = {"symbols": {"NIFTY": {"1m": {"bias": "BULLISH", "state": "LIVE_VERIFIED"}}}}
        out = {"market_open": True, "symbols": {"NIFTY": {"1m": {"bias": "BEARISH", "state": "LIVE_VERIFIED", "bullish": 30, "bearish": 70}}}}
        ev = mod.change_events(prev, out, 1000)
        self.assertEqual(ev[0]["from"], "BULLISH"); self.assertEqual(ev[0]["to"], "BEARISH")
        self.assertEqual(mod.change_events(prev, dict(out, market_open=False), 1000), [])
        self.assertEqual(mod.change_events(None, out, 1000), [])
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "j.jsonl"
            for i in range(5):
                mod.append_journal([{"t": i}] * 100, path)
            self.assertEqual(len(path.read_text().splitlines()), mod.JOURNAL_KEEP)

    def test_gateway_signal_routes_are_read_only_files(self):
        root = Path(__file__).resolve().parents[1]
        src = (root / "backend" / "clone_v2_gateway.py").read_text()
        self.assertIn('"/clone-v2/signals/latest"', src)
        self.assertIn('"/clone-v2/signals/journal"', src)
        seg = src[src.index("def read_private_text"):src.index("def paper_poll_once")]
        self.assertNotIn("post(", seg); self.assertNotIn("urlopen", seg)
        app = (root / "src" / "main.py").read_text()
        self.assertIn("server_away_section(),", app)


class B247AreaWatcherTests(unittest.TestCase):
    def _w(self, **kw):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
        from v3_smart_active_doctor import area_watch_issues
        base = dict(market_open=True, oracle_connected=True, ssk_saved=True, scanner_state="x",
                    scanner_busy=False, scanner_idle_seconds=10, chain_age=10, chain_symbol="NIFTY",
                    super_five_age=10, super_five_count=5, o_vote_age=10, watch_stalled_seconds=None)
        base.update(kw)
        return area_watch_issues(**base)

    def test_healthy_open_market_has_no_rows(self):
        self.assertEqual(self._w(), [])

    def test_closed_market_never_flags_ages(self):
        self.assertEqual(self._w(market_open=False, chain_age=9999, super_five_age=9999,
                                 scanner_idle_seconds=9999, o_vote_age=9999), [])

    def test_open_market_flags_each_stale_area(self):
        rows = self._w(chain_age=200, super_five_age=400, scanner_idle_seconds=1000,
                       o_vote_age=500, watch_stalled_seconds=90)
        self.assertEqual({r["point"] for r in rows}, {"OPTIONS_CHAIN_AGE", "SUPER_FIVE_STALE",
            "SCANNER_STUCK", "O_VOTE_AGE", "WATCHLIST_NO_PROGRESS"})
        self.assertTrue(all(r["next"] and r["reason"] and r["code"] for r in rows))

    def test_saved_ssk_but_disconnected(self):
        rows = self._w(oracle_connected=False)
        self.assertEqual(rows[0]["point"], "GATEWAY_SSK")


class B247InitialRenderOrderTests(unittest.TestCase):
    def test_names_used_by_first_home_render_exist_before_first_select(self):
        src = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text()
        first_select = src.index("\n    select(current[0])")
        for needle in ("    def server_away_section():", "    paper_hb_cache={}", "    area_stamps={"):
            self.assertLess(src.index(needle), first_select, needle)
        self.assertLess(src.index("    def server_away_section():"), src.index("    def dashboard():"))


class B248ChangePctTests(unittest.TestCase):
    def test_client_validates_and_exposes_change_pct(self):
        import importlib.util, io, json as _j
        root = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(root / "src"))
        spec = importlib.util.spec_from_file_location("phone_gw_b248", root / "src" / "clone_v2_gateway.py")
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        payload = {"source": "dhan", "freshness": "unverified", "live_orders_enabled": False, "unavailable": [],
                   "quotes": {"NIFTY": {"symbol": "NIFTY", "ltp": 25000.0, "source": "dhan", "freshness": "unverified", "change_pct": 0.75},
                              "SENSEX": {"symbol": "SENSEX", "ltp": 80000.0, "source": "dhan", "freshness": "unverified", "change_pct": 999}}}
        class Resp:
            status = 200
            def __init__(s): s.headers = type("H", (), {"get_content_type": lambda self: "application/json"})(); s.b = io.BytesIO(_j.dumps(payload).encode())
            def geturl(s): return "https://x.example/clone-v2/market/quotes"
            def read(s, n): return s.b.read(n)
            def __enter__(s): return s
            def __exit__(s, *a): return False
        class Op:
            def open(self, req, timeout=0): return Resp()
        g = mod.CloneV2Gateway(opener=Op()); g._origin = "https://x.example"; g._key = "k" * 40
        out = g.market_quotes(["NIFTY", "SENSEX"])
        self.assertEqual(mod.observed_quote_fields(out, "NIFTY")["change"], 0.75)
        self.assertIsNone(mod.observed_quote_fields(out, "SENSEX")["change"])  # absurd value rejected

    def test_server_adds_change_pct_from_net_change(self):
        src = (Path(__file__).resolve().parents[1] / "backend" / "clone_v2_gateway.py").read_text()
        self.assertIn('quotes[symbol]["change_pct"]', src)
        self.assertIn('.get("net_change")', src)
