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
        self.assertEqual(seg.count("authorized(x_botking_key)"), 4)
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
