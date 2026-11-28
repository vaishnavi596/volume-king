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

    def test_new_stop_after_average_trigger(self):
        e = eng()
        e.open_option("X", INST, 65, 1, 100, 50, 120, levels=[{"price": 70, "lots": 1}], target_avg=100,
                      expires_at=9e9, stop_avg=40)
        e.observe({"X": 69}); e.observe({"X": 45})
        self.assertEqual(len(e.open_positions()), 1)       # old SL 50 no longer applies
        e.observe({"X": 39})
        c = e.positions[-1]
        self.assertEqual((c["reason"], c["exit"], c["pnl"]), ("STOP_LOSS", 40.0, round((40 - 100) * 65 + (40 - 70) * 65, 2)))
        with self.assertRaises(ValueError):
            eng().open_option("Y", INST, 65, 1, 100, 50, 120, levels=[{"price": 70, "lots": 1}], stop_avg=75)

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


class LotPerExpiry(unittest.TestCase):
    def test_lot_by_expiry(self):
        import clone_signal_runner as r
        c = {"SENSEX|2026-12-03|72000|PE": ["BSE_FNO", 1, 20], "SENSEX|2027-03-25|76000|CE": ["BSE_FNO", 2, 25],
             "NIFTY|2026-12-02|24500|CE": ["NSE_FNO", 3, 65]}
        self.assertEqual(r.lot_by_expiry(c), {"SENSEX|2026-12-03": 20, "SENSEX|2027-03-25": 25, "NIFTY|2026-12-02": 65})
    def test_phone_prefers_per_expiry_lot(self):
        main = (pathlib.Path(__file__).parents[1] / "src" / "main.py").read_text()
        self.assertIn('lot_by_expiry', main)


class RosterChainPersistence(unittest.TestCase):
    def test_latest_pointer_accepted_and_wrong_symbol_rejected(self):
        sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "src"))
        from snapshot_store import SnapshotStore
        import tempfile, os
        payload = {"source": "dhan", "signal_eligible": False, "symbol": "TCS", "expiry": "2099-12-29", "pcr": 1.0}
        with tempfile.TemporaryDirectory() as d:
            st = SnapshotStore(pathlib.Path(d) / "c.json", incremental=True)
            self.assertTrue(st.put("option_context_last_good", ("Dhan", "TCS", "latest"), dict(payload)))
            self.assertTrue(st.put("option_context_last_good", ("Dhan", "TCS", "2099-12-29"), dict(payload)))
            self.assertFalse(st.put("option_context_last_good", ("Dhan", "INFY", "latest"), dict(payload)))
            self.assertEqual(st.get("option_context_last_good", "Dhan", "TCS", "latest")["symbol"], "TCS")
    def test_main_restores_latest_for_every_symbol(self):
        main = (pathlib.Path(__file__).parents[1] / "src" / "main.py").read_text()
        self.assertIn('("Dhan",sym,"latest")', main)
        self.assertIn('"option_context_last_good","Dhan",sym,"latest"', main)


class SingleSourceMaths(unittest.TestCase):
    def test_phone_estimate_equals_server_maths(self):
        import random
        sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "src"))
        import server_paper_positions as sp, option_ticket as ot
        random.seed(7)
        checked = 0
        for _ in range(400):
            e = random.uniform(50, 300); stop = e * random.uniform(.3, .9); tg = e * random.uniform(1.1, 2)
            lv = [{"price": e * random.uniform(.5, .95), "lots": random.randint(1, 3)} for _ in range(random.randint(0, 2))]
            lv = [x for x in lv if stop < x["price"] < e]
            a = sp.scenarios(e, 2, 65, lv, stop, tg, e * 1.05)
            b = ot.averaging_scenarios(e, 2, 65, [(x["price"], x["lots"]) for x in lv], stop, tg, e * 1.05)
            if not a["ok"]:
                continue
            key = lambda rows: [(x["lots"], x["avg"], x["invested"], x["loss_at_stop"], x["profit_at_target"]) for x in rows]
            self.assertEqual(key(a["rows"]), key(b)); checked += 1
        self.assertGreater(checked, 300)
    def test_bad_input_fails_closed(self):
        import server_paper_positions as sp
        self.assertFalse(sp.scenarios(100, 1, 65, [], 120, 130, None)["ok"])
        self.assertFalse(sp.scenarios(100, 1, 65, [{"price": 40, "lots": 1}], 50, 120, None)["ok"])
    def test_preview_wiring(self):
        root = pathlib.Path(__file__).parents[1]
        gw = (root / "backend" / "clone_v2_gateway.py").read_text()
        self.assertIn('"/clone-v2/paper/preview-option"', gw)
        self.assertIn("authorized(x_botking_key)", gw[gw.index("def paper_preview_option"):][:400])
        main = (root / "src" / "main.py").read_text()
        self.assertIn("tk_srv_preview", main)
        self.assertIn("सर्वर से जाँचा", main)


class TicketLayout(unittest.TestCase):
    def test_ticket_fields_have_no_fixed_width_and_skip_help_wrapper(self):
        import re
        main = (pathlib.Path(__file__).parents[1] / "src" / "main.py").read_text()
        for name in ("tk_lots", "tk_unit", "tk_sl_price", "tk_sl_pct", "tk_tg_price", "tk_tg_pct",
                     "tk_lv1_price", "tk_lv1_lots", "tk_lv2_price", "tk_lv2_lots", "tk_tga_price"):
            line = re.search(r"\n    %s=ft\.TextField\([^\n]*" % name, main).group(0)
            self.assertNotIn("width=", line, name)
            self.assertIn("expand=True", line, name)
        card = main[main.index("def ticket_card"):main.index("def ticket_card") + 4000]
        self.assertIn('data="compact_group"', card)


class StopAfterAveragingTests(unittest.TestCase):
    def test_new_stop_after_average(self):
        import server_paper_positions as sp
        eng = sp.PaperEngine(None) if False else None
        r = sp.scenarios(100, 1, 65, [{"price": 70, "lots": 1}], 50, 120, 100, 40)
        self.assertTrue(r["ok"])
        self.assertEqual(r["rows"][0]["stop"], 50.0)
        self.assertEqual(r["rows"][1]["stop"], 40.0)
        self.assertEqual(r["rows"][1]["loss_at_stop"], round((85 - 40) * 130, 2))
        bad = sp.scenarios(100, 1, 65, [{"price": 70, "lots": 1}], 50, 120, 100, 75)
        self.assertFalse(bad["ok"])

    def test_phone_matches_server(self):
        import option_ticket, server_paper_positions as sp
        a = sp.scenarios(100, 1, 65, [{"price": 70, "lots": 1}], 50, 120, 100, 40)["rows"]
        b = option_ticket.averaging_scenarios(100, 1, 65, [(70, 1)], 50, 120, 100, 40)
        self.assertEqual([x["loss_at_stop"] for x in a], [x["loss_at_stop"] for x in b])
