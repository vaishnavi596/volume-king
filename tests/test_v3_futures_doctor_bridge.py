"""Futures context must be user-initiated and Doctors cache-only."""
import pathlib,ast,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class FuturesDoctorWiringTests(unittest.TestCase):
    def test_explicit_readonly_futures_to_both_doctors(self):
        src=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
        ast.parse(src)
        self.assertIn('dhan_feed.futures_context,sym,listed',src)
        self.assertIn('futures_context_cache[(generation,sym,listed)]',src)
        self.assertIn('matching_futures_context_for_symbol(symbol)',src)
        self.assertIn('matching_futures_context_for_symbol(scanner_sym)',src)
        self.assertIn('futures_context_cache.clear()',src)
        self.assertIn('Check Futures Context (read-only)',src)
        for name in ("four_box_readiness","master_four_box_readiness"):
            self.assertIn(name+"=four_box_source_readiness(",src)
if __name__=="__main__":unittest.main()
