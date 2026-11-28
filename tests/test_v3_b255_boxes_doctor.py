import sys, unittest
sys.path[:0] = ["src", "backend"]
SRC = open("src/main.py", encoding="utf-8").read()
RUN = open("backend/clone_signal_runner.py", encoding="utf-8").read()
GW = open("backend/clone_v2_gateway.py", encoding="utf-8").read()


class BoxBase(unittest.TestCase):
    def test_runner_technical_vote_is_one_minute_only(self):
        self.assertIn('"box_base": "1m"', RUN)
        self.assertIn('one_m = (out["symbols"].get(symbol) or {}).get("1m")', RUN)
        self.assertNotIn("frame_b.count", RUN)

    def test_gate_rows_have_horizon_and_weight(self):
        import clone_signal_runner as r
        row = r._gate_row(40, 30, 55.0)
        self.assertTrue(row["eligible"]); self.assertGreater(row["weight"], 0)
        weak = r._gate_row(10, 5, None)
        self.assertEqual(weak["weight"], 0.0)
        g = r.vote_gate({"stats": {}}, {"next_day": {"NIFTY": {"n": 200, "hit_rate": 56.0, "up_rate": 53.0}}})
        self.assertEqual(g["D"]["horizon"], "next-day"); self.assertEqual(g["M"]["horizon"], "30-60m")
        self.assertEqual(g["O"]["horizon"], "day")


class Daily(unittest.TestCase):
    def test_gateway_has_read_only_daily_route(self):
        self.assertIn('"/clone-v2/market/daily"', GW)
        self.assertIn("provider().historical(args)", GW)

    def test_next_day_score(self):
        import clone_replay as c
        closes = [100 + i for i in range(40)]
        bars = [[i, x, x, x, x, 1] for i, x in enumerate(closes)]
        r = c.next_day_score(bars)
        self.assertEqual(r["hit_rate"], 100.0); self.assertEqual(r["up_rate"], 100.0)
        self.assertIsNone(c.next_day_score([[0, 1, 1, 1, 1, 1]]))


class DoctorPower(unittest.TestCase):
    def test_doctor_actions_and_report(self):
        import v3_doctor_repairs as d
        self.assertIn("refresh_news_boxes", d.ALLOWED_ACTIONS)
        self.assertEqual(d.MAJOR_ACTIONS, ("reconnect_saved_ssk",))
        for needle in ("BK-DOC-NEWS-EMPTY", "BK-DOC-SUMMARY-001", "doctor_research_errors", "doctor_ask_major",
                       "बड़े सुधार से पहले मुझसे पूछे", '"never_touched"'):
            self.assertIn(needle, SRC)
        self.assertNotIn("LIVE_ORDERS_ENABLED=True", SRC)

    def test_news_check_imports_its_counter(self):
        i = SRC.index("def doctor_news_ok(sym):")
        self.assertIn("from v3_four_box_source_readiness import valid_news_context_count", SRC[i:i + 300])

    def test_scrub_removes_secrets(self):
        import re
        t = re.sub(r"[A-Za-z0-9_\-]{24,}", "", "area: KeyError abcdefghijklmnopqrstuvwxyz0123")
        self.assertNotIn("abcdefghijklmnopqrstuvwxyz", t)


class EditOrders(unittest.TestCase):
    def _mgr(self):
        import server_paper_positions as sp, tempfile, os
        return sp.ServerPaper(os.path.join(tempfile.mkdtemp(), "p.json")) if hasattr(sp, "ServerPaper") else None

    def test_edit_protection_not_trade(self):
        import server_paper_positions as sp, tempfile, os
        cls = [v for v in vars(sp).values() if isinstance(v, type) and hasattr(v, "edit_levels")][0]
        m = cls(os.path.join(tempfile.mkdtemp(), "p.json"))
        pos = m.open_option("NIFTY 25000 CE", {"seg": "NSE_FNO", "sid": 1}, 75, 1, 100.0, None, None)
        self.assertIsNone(pos["stop"])
        m.observe({"NIFTY 25000 CE": 50.0})                       # no stop -> must stay open
        self.assertEqual(len(m.open_positions()), 1)
        out = m.edit_levels(pos["id"], {"stop": 80.0, "target": 130.0})
        self.assertEqual((out["stop"], out["target"]), (80.0, 130.0))
        with self.assertRaises(ValueError): m.edit_levels(pos["id"], {"qty": 5})
        with self.assertRaises(ValueError): m.edit_levels(pos["id"], {"stop": 120.0})
        with self.assertRaises(ValueError): m.edit_levels(pos["id"], {"stop": None})
        m.observe({"NIFTY 25000 CE": 79.0})
        self.assertEqual(len(m.open_positions()), 0)              # edited stop now protects
        with self.assertRaises(KeyError): m.edit_levels(pos["id"], {"stop": 70.0})

    def test_route_and_phone_wiring(self):
        self.assertIn('"/clone-v2/paper/edit"', GW)
        self.assertIn("def paper_edit_dialog(x):", SRC)
        self.assertIn('"सुधारें"', SRC)


if __name__ == "__main__":
    unittest.main()
