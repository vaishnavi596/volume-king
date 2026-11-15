"""T3 paper-only profit booking, fee buffer and independent risk policies."""
import unittest
from paper_engine import levels,evaluate_mark,pnl
from test_audit import start

class BreakEvenAndPaperChargesTests(unittest.TestCase):
    def base(self,side="BUY"):
        stop,target=levels(side,100,2,10)
        return {"side":side,"entry":100,"quantity":10,"unit_size":1,
                "stop_loss_pct":2,"target_pct":10,"stop_price":stop,"target_price":target}
    def test_break_even_buy_and_sell_fee_buffer(self):
        for side,mark,stop in (("BUY",104,100.5),("SELL",96,99.5)):
            with self.subTest(side=side):
                decision=evaluate_mark(self.base(side),mark,{
                    "breakeven":True,"breakeven_trigger":2,
                    "breakeven_fee_buffer":5})
                self.assertEqual(decision["action"],"HOLD")
                self.assertEqual(decision["position"]["stop_price"],stop)
    def test_break_even_cannot_move_stop_backward(self):
        p=self.base()
        p["stop_price"]=102
        d=evaluate_mark(p,104,{"breakeven":True,"breakeven_trigger":2})
        self.assertEqual(d["position"]["stop_price"],102)
    def test_break_even_disabled_is_backward_compatible(self):
        p=self.base()
        d=evaluate_mark(p,104,{})
        self.assertEqual(d["position"]["stop_price"],98)
    def test_net_partial_booking_includes_charges(self):
        _,v=start({"scanner_live":False,"bot_premium":100,"stop_loss":10,
                   "target":20,"max_trades":5,"max_total_lots":2})
        v["bot_paper_action"]("BUY")
        v["paper_run"]("Start")
        v["paper_mark"].value="95"
        v["buy_dip"].value=True
        v["paper_tick"]()
        self.assertEqual(v["bot_position"]["quantity"],2)
        v["paper_exit_fees"].value="1"
        v["partial_profit"].value=True
        v["paper_mark"].value="101"
        v["paper_tick"]()
        self.assertEqual(v["bot_position"]["quantity"],1)
        self.assertEqual(v["prefs"]["paper_journal"][-1]["event"],"PARTIAL")
        self.assertEqual(v["prefs"]["paper_journal"][-1]["charges"],1)
        self.assertEqual(v["prefs"]["paper_journal"][-1]["paper_pnl"],2.5)
        self.assertEqual(v["paper_risk_ledger"]()["realized_profit"],2.5)

if __name__=="__main__":
    unittest.main()
