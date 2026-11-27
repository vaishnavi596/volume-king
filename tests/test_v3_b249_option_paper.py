import sys, pathlib, unittest
sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "backend"))
from server_paper_positions import PaperEngine

INST = {"seg": "NSE_FNO", "sid": 12345}

def eng(t=[1000.0]):
    return PaperEngine(None, clock=lambda: t[0])

class OptionPaper(unittest.TestCase):
    def test_owner_example_average_then_target(self):
        e = eng()
        e.open_option("NIFTY 24500 CE", INST, 65, 1, 100, 50, 120,
                      levels=[{"price": 70, "lots": 1}], target_avg=100, expires_at=9e9)
        self.assertEqual(e.observe({"NIFTY 24500 CE": 90}), [])           # no level yet
        e.observe({"NIFTY 24500 CE": 69})                                   # level hit
        p = e.open_positions()[0]
        self.assertTrue(p["averaged"]); self.assertEqual(p["qty"], 130); self.assertEqual(p["entry"], 85.0)
        self.assertEqual(e.observe({"NIFTY 24500 CE": 110}) and 1, 1)       # >=100 closes at averaged target
        c = e.positions[-1]
        self.assertEqual((c["reason"], c["exit"], c["pnl"]), ("TARGET", 100.0, 1950.0))

    def test_no_average_uses_plain_target(self):
        e = eng()
        e.open_option("X", INST, 65, 1, 100, 50, 120, levels=[{"price": 70, "lots": 1}], target_avg=100, expires_at=9e9)
        e.observe({"X": 121})
        c = e.positions[-1]
        self.assertEqual((c["reason"], c["exit"], c["pnl"]), ("TARGET", 120.0, 1300.0))

    def test_stop_after_average_uses_total_qty(self):
        e = eng()
        e.open_option("X", INST, 65, 1, 100, 50, 120, levels=[{"price": 70, "lots": 1}], target_avg=100, expires_at=9e9)
        e.observe({"X": 69}); e.observe({"X": 49})
        c = e.positions[-1]
        self.assertEqual((c["reason"], c["exit"], c["pnl"]), ("STOP_LOSS", 50.0, -4550.0))

    def test_gap_below_stop_does_not_average(self):
        e = eng()
        e.open_option("X", INST, 65, 1, 100, 50, 120, levels=[{"price": 70, "lots": 1}], expires_at=9e9)
        e.observe({"X": 40})
        c = e.positions[-1]
        self.assertEqual((c["reason"], c["pnl"]), ("STOP_LOSS", -3250.0))

    def test_levels_expire(self):
        t = [1000.0]; e = PaperEngine(None, clock=lambda: t[0])
        e.open_option("X", INST, 65, 1, 100, 50, 120, levels=[{"price": 70, "lots": 1}], expires_at=1500.0)
        t[0] = 2000.0
        e.observe({"X": 69})
        self.assertFalse(e.open_positions()[0]["averaged"])

    def test_validation(self):
        e = eng()
        bad = [dict(stop=110, target=120), dict(stop=50, target=90),
               dict(stop=50, target=120, levels=[{"price": 40, "lots": 1}]),
               dict(stop=50, target=120, levels=[{"price": 110, "lots": 1}]),
               dict(stop=50, target=120, levels=[{"price": 70, "lots": 1}], target_avg=80),
               dict(stop=50, target=120, target_avg=100)]
        for kw in bad:
            with self.assertRaises(ValueError):
                e.open_option("X", INST, 65, 1, 100, kw.pop("stop"), kw.pop("target"), **kw)
        with self.assertRaises(ValueError):
            e.open_option("X", {"seg": "NSE_FNO"}, 65, 1, 100, 50, 120)

    def test_instruments_exposed_for_poller(self):
        e = eng()
        e.open_option("NIFTY 24500 CE", INST, 65, 1, 100, 50, 120)
        self.assertEqual(e.open_instruments(), {"NIFTY 24500 CE": ("NSE_FNO", 12345)})

if __name__ == "__main__":
    unittest.main()


class Contracts(unittest.TestCase):
    def test_parse_contracts_nearest_expiries_and_segments(self):
        import clone_signal_runner as r
        H = "SEM_EXM_EXCH_ID,SEM_SMST_SECURITY_ID,SEM_INSTRUMENT_NAME,SEM_TRADING_SYMBOL,SEM_LOT_UNITS,SEM_EXPIRY_DATE,SEM_STRIKE_PRICE,SEM_OPTION_TYPE"
        rows = [H]
        for i, d in enumerate(("2026-12-02", "2026-12-09", "2026-12-16", "2026-12-23")):
            rows.append("NSE,%d,OPTIDX,NIFTY-X-24500-CE,65.0,%s 14:30:00,24500.0,CE" % (100 + i, d))
        rows.append("BSE,900,OPTIDX,SENSEX-X-80000-PE,25.0,2026-12-04 14:30:00,80000.0,PE")
        rows.append("NSE,5,OPTIDX,NIFTY-X-24500-CE,65.0,2026-11-20 14:30:00,24500.0,CE")  # expired
        rows.append("NSE,6,OPTSTK,RELIANCE-X-1500-CE,500.0,2026-12-30 14:30:00,1500.0,CE")
        out = r.parse_option_contracts(rows, "2026-11-28")
        self.assertEqual(out["NIFTY|2026-12-02|24500|CE"], ["NSE_FNO", 100, 65])
        self.assertNotIn("NIFTY|2026-12-23|24500|CE", out)
        self.assertEqual(out["SENSEX|2026-12-04|80000|PE"], ["BSE_FNO", 900, 25])
        self.assertEqual(len(out), 4)

class GatewayContract(unittest.TestCase):
    def test_route_and_poller_wiring(self):
        src = (pathlib.Path(__file__).parents[1] / "backend" / "clone_v2_gateway.py").read_text()
        self.assertIn('"/clone-v2/paper/open-option"', src)
        self.assertIn("paper.open_instruments()", src)
        self.assertIn("Market closed: option paper entry needs a live premium", src)
        self.assertIn("authorized(x_botking_key)", src[src.index("def paper_open_option"):][:300])
        self.assertIn('"live_orders_enabled"', src)
        import importlib.util
        try:
            spec = importlib.util.spec_from_file_location(
                "backend_gateway_b249", str(pathlib.Path(__file__).parents[1] / "backend" / "clone_v2_gateway.py"),
                submodule_search_locations=None)
            g = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(g)
        except ImportError:
            self.skipTest("fastapi only in CI")
        import datetime
        t = datetime.datetime(2026, 11, 30, 10, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
        self.assertEqual(datetime.datetime.fromtimestamp(g.option_levels_expiry(t), datetime.timezone(datetime.timedelta(hours=5, minutes=30))).strftime("%H:%M"), "15:30")


class PhoneWiring(unittest.TestCase):
    def test_ticket_wiring(self):
        root = pathlib.Path(__file__).parents[1]
        main = (root / "src" / "main.py").read_text()
        gw = (root / "src" / "clone_v2_gateway.py").read_text()
        for needle in ("tk_lv1_price", "tk_tga_price", "averaging_scenarios", "paper_open_option",
                       "औसत पर टारगेट"):
            self.assertIn(needle, main)
        self.assertIn('"open-option"', gw)
        self.assertLess(main.index("tk_lv1_price=ft.TextField"), main.index("\n    select(current[0])"))
    def test_scenarios_owner_example(self):
        sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "src"))
        import option_ticket as t
        rows = t.averaging_scenarios(100, 1, 65, [(70, 1)], 50, 120, 100)
        self.assertEqual((rows[0]["loss_at_stop"], rows[0]["profit_at_target"]), (3250.0, 1300.0))
        self.assertEqual((rows[1]["avg"], rows[1]["invested"], rows[1]["loss_at_stop"], rows[1]["profit_at_target"]),
                         (85.0, 11050.0, 4550.0, 1950.0))
