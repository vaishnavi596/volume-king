"""Dhan CE/PE display fields must be measured and never become a trade signal."""
from pathlib import Path
import unittest

SOURCE=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
class OptionWindowDisplay127(unittest.TestCase):
    def test_both_sides_show_OI_delta_only_when_available(self):
        block=SOURCE.split('    def option_chain_preview():',1)[1].split('    def options():',1)[0]
        self.assertIn('value(item["ce"],"last_price",2)',block)
        self.assertIn('value(item["pe"],"last_price",2)',block)
        self.assertIn('oi_change(item["ce"])',block)
        self.assertIn('oi_change(item["pe"])',block)
        self.assertIn('previous_oi=leg.get("previous_oi")',block)
        self.assertIn('return "—"',block)
        self.assertIn('current_oi-previous_oi',block)
        self.assertIn('"CE ΔOI"',block)
        self.assertIn('"PE ΔOI"',block)
        self.assertIn('NOT traded cash',block)

    def test_option_remains_display_only(self):
        block=SOURCE.split('    def option_chain_preview():',1)[1].split('    def options():',1)[0]
        self.assertIn('context.get("available")',block)
        self.assertIn('signals WAIT',block)
        self.assertIn('live orders OFF',block)

if __name__=="__main__":
    unittest.main()
