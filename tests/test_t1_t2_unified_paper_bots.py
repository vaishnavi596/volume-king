"""T1/T2: movable paper trading controls + isolated durable paper bot slots."""
import unittest
from paper_bot_slots import SLOTS,bootstrap,load_slot,save_slot,record,positions_summary
from test_audit import start


class PaperSlotUnitTests(unittest.TestCase):
    def test_legacy_migration_is_idempotent(self):
        state={"bot_position":{"side":"BUY","entry":100,"quantity":2,"contract":"RELIANCE CASH"}}
        positions=bootstrap(state)
        self.assertEqual(len(positions),5)
        self.assertEqual(positions["Bot 1"]["contract"],"RELIANCE CASH")
        self.assertIsNone(positions["Bot 2"]["side"])
        self.assertEqual(bootstrap(state)["Bot 1"]["quantity"],2)

    def test_isolated_positions_and_config(self):
        state={}
        save_slot(state,"Bot 1",{"side":"BUY","contract":"NIFTY CE","quantity":75},{"bot_symbol":"NIFTY","bot_premium":"100"})
        save_slot(state,"Bot 2",{"side":"SELL","contract":"BANKNIFTY PE","quantity":30},{"bot_symbol":"BANKNIFTY","bot_premium":"200"})
        p1,c1=load_slot(state,"Bot 1")
        p2,c2=load_slot(state,"Bot 2")
        self.assertNotEqual(p1["contract"],p2["contract"])
        self.assertEqual(c1["bot_premium"],"100")
        self.assertEqual(c2["bot_premium"],"200")
        self.assertEqual(len(positions_summary(state)),5)
        with self.assertRaises(ValueError):save_slot(state,"Live Bot",{}, {})

    def test_bounded_paper_only_journal(self):
        state={}
        for i in range(320):
            row=record(state,"Bot 1","BUY",{"contract":"NIFTY","quantity":1},price=100)
            self.assertEqual(row["kind"],"paper_simulation")
        self.assertEqual(len(state["paper_portfolio_journal"]),300)
        with self.assertRaises(ValueError):
            record(state,"Bot 1","EXIT",{},charges=-1)

class PaperTradingCenterUITests(unittest.TestCase):
    def test_options_contains_paper_controls_without_live_order(self):
        _,v=start({"scanner_live":False,"source":"Dhan","last_page":1})
        controls=v["options"]()
        def captions(control):
            yield str(getattr(control,"text",None) or getattr(control,"value",None) or "")
            for child in control._get_children():
                yield from captions(child)
        text=" ".join(piece for control in controls for piece in captions(control))
        # B252 layout (owner): the old dummy paper centre is gone from Options; BUY is the last, only order action
        self.assertNotIn("TRADING CENTER",text)
        self.assertNotIn("PAPER BOT",text)
        self.assertIn("BUY",text)
        self.assertNotIn("LIVE TRADING ON",text.upper())

    def test_independent_bot_switch_and_restore(self):
        page,v=start({"scanner_live":False,"source":"Dhan","last_page":1})
        v["bot_paper_action"]("BUY")
        original=v["bot_position"].get("contract")
        slot=v["paper_bot_slot"]
        slot.value="Bot 2"
        v["switch_paper_bot"](type("E",(),{"control":slot})())
        self.assertIsNone(v["bot_position"].get("side"))
        v["bot_segment"].value="Cash"
        v["bot_symbol"].value="RELIANCE"
        v["bot_premium"].value="100"
        v["bot_paper_action"]("BUY")
        self.assertIn("RELIANCE",str(v["bot_position"].get("contract")))
        slot.value="Bot 1"
        v["switch_paper_bot"](type("E",(),{"control":slot})())
        self.assertEqual(v["bot_position"].get("contract"),original)
        self.assertEqual(v["paper_bot_state"],["Stopped"])
        saved=page.client_storage.get("bot_king_preferences")
        self.assertIn("Bot 2",saved["paper_bot_positions"])


if __name__=="__main__":
    unittest.main()
