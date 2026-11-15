"""Central filter slots: user can swap ten saved filters without claiming OI data is live."""
import unittest

from test_audit import start
from scanner_engine import DEFAULT_FILTERS, OPTION_FILTERS


class CentralFilterSlotsTests(unittest.TestCase):
    def test_remove_three_and_add_three_oi_filters_and_restore(self):
        _, v = start({"source":"Dhan","scanner_live":False,"last_page":2})
        self.assertEqual(len(v["filter_selected"]),10)
        removed=DEFAULT_FILTERS[:3]
        for name in removed:
            v["remove_added_filter"](name)
        self.assertEqual(len(v["filter_selected"]),7)
        page=v["central_filter_settings"]()
        self.assertIsNotNone(page)
        self.assertEqual(len(v["filter_checklist"].controls),7)
        self.assertIn("OI Support",[opt.key for opt in v["filter_choice"].options])
        for name in ("OI Support","OI Resistance","Max Pain"):
            v["add_filter_slot"](name)
        self.assertEqual(len(v["filter_selected"]),10)
        self.assertTrue(set(removed).isdisjoint(v["filter_selected"]))
        self.assertTrue({"OI Support","OI Resistance","Max Pain"}.issubset(v["filter_selected"]))
        self.assertEqual(v["prefs"]["scanner_filters"],v["filter_selected"])
        _,restored=start({"source":"Dhan","scanner_live":False,"last_page":2,
                          "scanner_filters":v["prefs"]["scanner_filters"],
                          "default_ten_migrated":True})
        self.assertEqual(restored["filter_selected"],v["filter_selected"])

    def test_full_slots_prevent_eleventh_and_available_includes_removed_defaults(self):
        _,v=start({"source":"Dhan","scanner_live":False,"last_page":2})
        v["add_filter_slot"]("OI Profile")
        self.assertEqual(len(v["filter_selected"]),10)
        self.assertIn("10/10 slots full",v["filter_feedback"].value)
        v["remove_added_filter"]("VWAP")
        screen=v["central_filter_settings"]()
        self.assertIn("VWAP",[opt.key for opt in v["filter_choice"].options])
        self.assertNotIn("VWAP",v["filter_selected"])
        v["add_filter_slot"]("OI Profile")
        self.assertIn("OI Profile",v["filter_selected"])
        self.assertEqual(len(v["filter_selected"]),10)

    def test_option_filters_remain_saved_but_not_verified_vote(self):
        _,v=start({"source":"Dhan","scanner_live":False,"last_page":2,
                   "scanner_filters":["EMA 9/21","OI Support","OI Resistance","Max Pain"],
                   "default_ten_migrated":True})
        self.assertEqual(v["filter_selected"],["EMA 9/21","OI Support","OI Resistance","Max Pain"])
        for name in OPTION_FILTERS:
            self.assertIn("WAITING FOR DATA",v["filter_availability"](name))
        self.assertEqual(v["prefs"]["scanner_filters"],v["filter_selected"])


if __name__=="__main__":
    unittest.main()
