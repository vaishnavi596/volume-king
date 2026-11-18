"""Five local PAPER planning slots: separate, strict and non-executing."""
import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(ROOT))
from local_paper_slots import LocalPaperPlanSlots, PaperSlotError, SLOTS
from paper_preview import preview_manual_paper_risk


class PaperPlanSlotTests(unittest.TestCase):
    def test_five_independent_manual_risk_previews_roundtrip(self):
        state = LocalPaperPlanSlots()
        self.assertEqual(SLOTS, ("Bot 1", "Bot 2", "Bot 3", "Bot 4", "Bot 5"))
        state.save_preview(preview_manual_paper_risk("BUY", 100, 2, 2, 4, 10000, 1000, 5))
        state.choose("Bot 3")
        state.save_preview(preview_manual_paper_risk("SELL", 200, 3, 2, 4, 10000, 1000, 5))
        self.assertIsNone(state.previews["Bot 2"])
        self.assertIsNone(state.previews["Bot 4"])
        restored = LocalPaperPlanSlots.from_saved(state.saved_state())
        self.assertEqual(restored.selected_slot, "Bot 3")
        self.assertEqual(restored.previews, state.previews)
        self.assertNotEqual(restored.previews["Bot 1"], restored.previews["Bot 3"])
        restored.clear()
        self.assertIsNone(restored.previews["Bot 3"])
        self.assertIsNotNone(restored.previews["Bot 1"])

    def test_no_orders_positions_or_unknown_settings_accepted(self):
        obj = LocalPaperPlanSlots()
        base = obj.saved_state()
        for value in ("Bot 6", "unknown", "", None, True):
            with self.assertRaises(PaperSlotError):
                obj.choose(value)
        for k in ("api_key", "token", "server_url", "live_orders_enabled"):
            changed = dict(base)
            changed[k] = "forbidden"
            with self.assertRaises(PaperSlotError):
                LocalPaperPlanSlots.from_saved(changed)
        changed = obj.saved_state()
        changed["previews"]["Bot 2"] = {"side": "BUY", "entry": 100}
        with self.assertRaises(PaperSlotError):
            LocalPaperPlanSlots.from_saved(changed)
        with self.assertRaises(PaperSlotError):
            obj.save_preview({"status": "LIVE", "orders_enabled": True, "live_verified": True})

    def test_real_flet_settings_controls_no_broker_calls(self):
        s = (ROOT / "main.py").read_text()
        ast.parse(s)
        for needle in ('from local_paper_slots import LocalPaperPlanSlots',
                       "paper_slots = [LocalPaperPlanSlots",
                       "def choose_paper_slot(e):",
                       "def save_paper_slot(e):",
                       "def clear_paper_slot(e):",
                       'label="Paper planning slot"',
                       'ft.TextButton("Save PAPER preview to slot"',
                       'ft.TextButton("Clear selected PAPER preview"'):
            self.assertIn(needle, s)
        for forbidden in ("submit_order(", "place_order(", "ServerAngelFeed(", "get_yahoo("):
            self.assertNotIn(forbidden, s)
        self.assertEqual(s.count("ft.NavigationDestination("), 3)


if __name__ == "__main__":
    unittest.main()
