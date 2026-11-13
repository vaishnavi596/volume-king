"""Guard quote provenance when the active provider changes."""
from pathlib import Path
import unittest

SOURCE=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")

class ProviderCacheBoundaryTests(unittest.TestCase):
    def test_previous_quotes_require_selected_source(self):
        body=SOURCE.split('    def provider_changed(e):',1)[1].split('    broker_previous=',1)[0]
        self.assertIn('row.get("source")==cached_source',body)
        self.assertIn('dict(row,freshness="unverified")',body)

    def test_persisted_quotes_also_require_selected_source(self):
        body=SOURCE.split('    def provider_changed(e):',1)[1].split('    broker_previous=',1)[0]
        self.assertIn('if row.get("source")==cached_source',body)

    def test_source_map_remains_explicit(self):
        body=SOURCE.split('    def provider_changed(e):',1)[1].split('    broker_previous=',1)[0]
        self.assertIn('"Broker API":"Angel One"',body)
        self.assertIn('"Dhan":"Dhan"',body)

if __name__=="__main__":
    unittest.main()
