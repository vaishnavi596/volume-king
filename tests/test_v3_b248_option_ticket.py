import unittest, pathlib
import option_ticket as t

class Ticket(unittest.TestCase):
    def test_owner_example(self):
        self.assertEqual(t.price_from_pct(90, 4, "BUY", "sl"), 86.4)
        self.assertEqual(t.pct_from_price(90, 120, "BUY", "tg"), 33.33)
        r = t.ticket_summary(90, "BUY", 1, 75, 86.4, 120)
        self.assertEqual((r["loss"], r["profit"], r["rr"], r["max_loss"]), (270.0, 2250.0, 8.3, 6750.0))
    def test_wrong_side_rejected(self):
        self.assertIsNone(t.pct_from_price(90, 95, "BUY", "sl"))
        self.assertFalse(t.ticket_summary(90, "BUY", 1, 75, 95, 80)["sl_ok"])
    def test_sell_mirrored(self):
        self.assertEqual(t.price_from_pct(100, 10, "SELL", "sl"), 110.0)
        self.assertEqual(t.price_from_pct(100, 10, "SELL", "tg"), 90.0)
    def test_invalid(self):
        self.assertFalse(t.ticket_summary("", "BUY", 1, 75, 1, 2)["valid"])
        self.assertFalse(t.ticket_summary(90, "BUY", 0, 75, 1, 2)["valid"])
        self.assertIsNone(t.price_from_pct(90, "x", "BUY", "sl"))
    def test_main_wiring_and_no_order(self):
        src = (pathlib.Path(__file__).parents[1] / "src" / "main.py").read_text()
        self.assertIn("import option_ticket", src)
        self.assertIn("ticket_card()", src)
        self.assertIn("on_tap=_tap(", src)
        i = src.index("def ticket_place"); seg = src[i:i + 400]
        self.assertNotIn("paper_open", seg)
        self.assertLess(src.index("def ticket_pick"), src.index("\n    select(current[0])"))
if __name__ == "__main__":
    unittest.main()

class WindowTolerance(unittest.TestCase):
    def test_one_leg_strikes_are_skipped_not_fatal(self):
        import sys, pathlib
        sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "backend"))
        import dhan_option_metrics as m
        oc = {}
        for k in range(48000, 49500, 100):
            oc[f"{k}.000000"] = {"ce": {"oi": 10, "last_price": 5.0}, "pe": {"oi": 11, "last_price": 6.0}}
        oc["48350.000000"] = {"ce": {"oi": 10, "last_price": 5.0}}  # PE missing
        r = m.listed_atm_window({"status": "success", "data": {"oc": oc}}, spot=48400)
        rows = r["rows"]
        self.assertEqual(len(rows), 7)
        self.assertNotIn(48350.0, [x["strike"] for x in rows])
