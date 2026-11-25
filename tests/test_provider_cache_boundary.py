"""Guard quote provenance when the active provider changes."""
from pathlib import Path
import unittest

SOURCE=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")

class ProviderCacheBoundaryTests(unittest.TestCase):
    def test_previous_quotes_require_selected_source(self):
        body=SOURCE.split('    def provider_changed(e):',1)[1].split('    broker_previous=',1)[0]
        self.assertIn('quotes.update(restored_quote_rows(previous_quotes,source=cached_source))',body)
        from v3_market_display_mode import restored_quote_rows
        rows = {"TCS": dict(source="Dhan", price=100, live_verified=True),
                "INFY": dict(source="Yahoo Finance", price=100, live_verified=True)}
        restored = restored_quote_rows(rows, source="Dhan")
        self.assertEqual(set(restored), {"TCS"})
        self.assertFalse(restored["TCS"]["live_verified"])
        self.assertEqual(restored["TCS"]["freshness"], "unverified")
        self.assertTrue(restored["TCS"]["cached"])

    def test_persisted_quotes_also_require_selected_source(self):
        body=SOURCE.split('    def provider_changed(e):',1)[1].split('    broker_previous=',1)[0]
        self.assertIn('quotes.update(restored_quote_rows(market_store.latest_markets(),source=cached_source))',body)
        from v3_market_display_mode import restored_quote_rows
        rows = {"TCS": dict(source="Dhan", price=100, live_verified=True),
                "INFY": dict(source="Dhan", symbol="TCS", price=100),
                "SBIN": dict(source="Angel One", price=100)}
        restored = restored_quote_rows(rows, source="Dhan")
        self.assertEqual(set(restored), {"TCS"})
        self.assertFalse(restored["TCS"]["live_verified"])
        self.assertEqual(restored["TCS"]["freshness"], "unverified")
        self.assertTrue(restored["TCS"]["cached"])

    def test_source_map_remains_explicit(self):
        body=SOURCE.split('    def provider_changed(e):',1)[1].split('    broker_previous=',1)[0]
        self.assertIn('"Broker API":"Angel One"',body)
        self.assertIn('"Dhan":"Dhan"',body)

if __name__=="__main__":
    unittest.main()
