"""Synthetic Flet V2 Scanner choice and saved roster guards (no broker)."""
import importlib.util
import sys
from pathlib import Path
import unittest

root = Path(__file__).resolve().parents[1] / "android_app" / "src"
def load(name):
    spec = importlib.util.spec_from_file_location(name + "_scanner_test",root / (name+".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

watch = load("app_state")
scanner = load("scanner_state")

class ScannerAppTests(unittest.TestCase):
    def test_index_default_and_app_owned_selected_equities(self):
        l = watch.LocalWatchlists()
        self.assertEqual(scanner.selectable_symbols(l), scanner.INDEXES)
        self.assertEqual(scanner.ScannerSelection(), scanner.ScannerSelection("NIFTY","1m"))
        l.add(0,"TCS")
        l.add(3,"INFY")
        self.assertEqual(scanner.selectable_symbols(l), scanner.INDEXES+("INFY","TCS"))
        choice=scanner.choose(scanner.ScannerSelection(),l,symbol="INFY",timeframe="3m")
        self.assertEqual(choice,scanner.ScannerSelection("INFY","3m"))
        self.assertEqual(scanner.ScannerSelection.from_saved(choice.saved_state(),l),choice)

    def test_deleted_or_unselected_symbol_rejected_not_scanned(self):
        l = watch.LocalWatchlists()
        with self.assertRaises(scanner.ScannerError):
            scanner.choose(scanner.ScannerSelection(),l,symbol="TCS")
        l.add(1,"TCS")
        v=scanner.choose(scanner.ScannerSelection(),l,symbol="TCS")
        l.remove(1,"TCS")
        self.assertEqual(scanner.for_visible_roster(v,l),scanner.ScannerSelection())
        with self.assertRaises(scanner.ScannerError):
            scanner.ScannerSelection.from_saved(v.saved_state(),l)

    def test_corrupt_saved_values_fail_closed(self):
        l=watch.LocalWatchlists()
        good=scanner.ScannerSelection().saved_state()
        samples=[None, {}, {"schema_version":True,"symbol":"NIFTY","timeframe":"1m"},
                 {"schema_version":1,"symbol":"RELIANCE","timeframe":"1m"},
                 {"schema_version":1,"symbol":"NIFTY","timeframe":"15m"},
                 dict(good,access_token="bad")]
        for bad in samples:
            with self.subTest(bad=repr(bad)),self.assertRaises(scanner.ScannerError):
                scanner.ScannerSelection.from_saved(bad,l)
        self.assertEqual(scanner.ScannerSelection.from_saved(good,l),scanner.ScannerSelection())

if __name__=="__main__":
    unittest.main()
