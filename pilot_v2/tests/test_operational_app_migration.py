"""One V2 app-side operational migration batch: safe paper ledger + refresh UI."""
import ast
import sys
import unittest
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from local_paper_ledger import ManualPaperLedger, PaperLedgerError
from local_paper_slots import LocalPaperPlanSlots
from paper_preview import preview_manual_paper_risk
from app_state import LocalWatchlists
from refresh_intent import make_refresh_intent
from smart_data import SmartDataSettings

class OperationalMigrationTests(unittest.TestCase):
    def setUp(self):
        self.ledger = ManualPaperLedger()
        self.slots = LocalPaperPlanSlots()
        self.slots.save_preview(preview_manual_paper_risk(
            "BUY", 100, 2, 2, 4, 10000, 1000, 5))

    def test_simulated_manual_entry_exit_only(self):
        saved = self.slots.previews["Bot 1"]
        with self.assertRaises(PaperLedgerError):
            self.ledger.open_simulation("Bot 1", saved)
        self.assertTrue(self.ledger.open_simulation(
            "Bot 1", saved, confirmed=True))
        with self.assertRaises(PaperLedgerError):
            self.ledger.open_simulation("Bot 1", saved, confirmed=True)
        with self.assertRaises(PaperLedgerError):
            self.ledger.close_simulation("Bot 1", 103)
        with self.assertRaises(PaperLedgerError):
            self.ledger.close_simulation("Bot 1", "nan", confirmed=True)
        self.assertIsNotNone(self.ledger.open_rows()[0][1])
        record = self.ledger.close_simulation(
            "Bot 1", 103, confirmed=True)
        self.assertEqual(record["paper_pnl"], 6)
        self.assertFalse(record["orders_enabled"])
        self.assertFalse(record["verified_live"])
        self.assertIsNone(self.ledger.open_rows()[0][1])

    def test_sell_loss_and_independent_slots(self):
        self.slots.choose("Bot 3")
        self.slots.save_preview(preview_manual_paper_risk(
            "SELL", 200, 3, 2, 4, 10000, 1000, 5))
        self.ledger.open_simulation("Bot 3",
            self.slots.previews["Bot 3"], confirmed=True)
        result=self.ledger.close_simulation("Bot 3", 202, confirmed=True)
        self.assertEqual(result["paper_pnl"], -6)
        self.assertEqual(result["source"], "manual_simulation")
        self.assertEqual(len(self.ledger.closed_rows()), 1)
        self.ledger.clear_closed()
        self.assertEqual(self.ledger.closed_rows(), ())

    def test_no_invalid_plan_broker_or_unapproved_roster(self):
        for invalid in (None, {}, {"orders_enabled": True}):
            with self.assertRaises(PaperLedgerError):
                self.ledger.open_simulation(
                    "Bot 2", invalid, confirmed=True)
        with self.assertRaises(PaperLedgerError):
            self.ledger.open_simulation(
                "Bot 6", self.slots.previews["Bot 1"], confirmed=True)
        w = LocalWatchlists()
        for idx in range(5):
            w.add(idx, "EQ" + str(idx))
        intent = make_refresh_intent(
            w, SmartDataSettings(),
            datetime(2026, 11, 19, 18, 0,
                     tzinfo=ZoneInfo("Asia/Kolkata")),
            manual=True, confirmed_session=False)
        self.assertEqual(len(intent.equities), 5)
        self.assertEqual(len(intent.indexes), 3)

    def test_real_source_controls_and_never_broker_order(self):
        src = (SRC / "main.py").read_text()
        tree = ast.parse(src)
        self.assertEqual(len([node for node in ast.walk(tree)
                         if isinstance(node, ast.FunctionDef)
                         and node.name == "preview_manual_refresh"]), 1)
        self.assertEqual(src.count("on_click=preview_manual_refresh"), 2)
        self.assertIn('history_view=scanner_history', src)
        self.assertIn("ledger.open_simulation(", src)
        self.assertIn("ledger.close_simulation(", src)
        self.assertIn('label="Confirm manual PAPER simulation"', src)
        self.assertIn('ft.TextButton("Open PAPER simulation"', src)
        self.assertIn('ft.TextButton("Close PAPER simulation"', src)
        for bad in ("submit_order(", "place_order(", "ServerAngelFeed(", "get_yahoo("):
            self.assertNotIn(bad, src)
        self.assertEqual(src.count("ft.NavigationDestination("), 3)

if __name__ == "__main__":
    unittest.main()
