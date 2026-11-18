"""V1 Dashboard three selectable analysis slots, offline V2 migration."""
import ast
import sys
import unittest
from pathlib import Path
SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from app_state import LocalWatchlists
from local_analysis_slots import LocalAnalysisSlots, AnalysisSlotError, SLOT_DEFAULTS


class DashboardAnalysisSlotsTests(unittest.TestCase):
    def test_three_independent_saved_slots_and_validated_equities(self):
        wl = LocalWatchlists()
        wl.add(0, "TCS")
        wl.add(1, "INFY")
        state = LocalAnalysisSlots()
        self.assertEqual(tuple(state.slots), SLOT_DEFAULTS)
        self.assertTrue(state.select(1, "TCS", wl))
        self.assertTrue(state.select(2, "INFY", wl))
        self.assertFalse(state.select(1, "TCS", wl))
        self.assertEqual(state.slots, ["NIFTY", "TCS", "INFY"])
        saved = state.saved_state()
        self.assertEqual(LocalAnalysisSlots.from_saved(saved, wl).slots, state.slots)
        for symbol in ("UNKNOWN", "", None):
            with self.assertRaises(AnalysisSlotError):
                state.select(0, symbol, wl)
        for index in (-1, 3, True, "1"):
            with self.assertRaises(AnalysisSlotError):
                state.select(index, "TCS", wl)

    def test_removed_symbol_reconciles_without_leaking_cross_slot(self):
        wl = LocalWatchlists()
        wl.add(0, "TCS")
        slots = LocalAnalysisSlots()
        slots.select(1, "TCS", wl)
        old_saved = slots.saved_state()
        wl.remove(0, "TCS")
        with self.assertRaises(AnalysisSlotError):
            LocalAnalysisSlots.from_saved(old_saved, wl)
        self.assertTrue(slots.reconcile(wl))
        self.assertEqual(slots.slots, list(SLOT_DEFAULTS))
        self.assertFalse(slots.reconcile(wl))

    def test_invalid_save_does_not_silently_restore_credentials_or_slots(self):
        wl = LocalWatchlists()
        for saved in (None, {}, {"schema_version": 1, "slots": ["TCS"]},
                      {"schema_version": True, "slots": list(SLOT_DEFAULTS)},
                      {"schema_version": 1, "slots": list(SLOT_DEFAULTS),
                       "token": "must_not_store"}):
            with self.assertRaises(AnalysisSlotError):
                LocalAnalysisSlots.from_saved(saved, wl)

    def test_actual_three_slot_controls_share_filter_context_and_one_minute(self):
        code = (SRC / "main.py").read_text(encoding="utf-8")
        ast.parse(code)
        for expected in ("from local_analysis_slots import LocalAnalysisSlots",
                         "analysis_slots = [LocalAnalysisSlots", "def select_analysis_slot(e, slot):",
                         "def open_analysis_chart(symbol):",
                         'label=f"Analysis {slot+1} · index/equity"',
                         'analysis_slots[0].slots[slot]',
                         'shared_filter_context(filter_evidence, symbol, "1m"',
                         'timeframe="1m"', "on_change=lambda e, slot=slot: select_analysis_slot(e, slot)"):
            self.assertIn(expected, code)
        self.assertEqual(code.count("ft.NavigationDestination("), 3)
        for forbidden in ("ServerAngelFeed(", "get_yahoo(", "submit_order("):
            self.assertNotIn(forbidden, code)

if __name__ == "__main__":
    unittest.main()
