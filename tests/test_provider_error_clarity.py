"""Provider errors must distinguish stale selection from broker disconnection."""
import pathlib
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "src" / "main.py"


class ProviderErrorClarityTests(unittest.TestCase):
    def test_unknown_provider_does_not_suggest_angel_fallback(self):
        source = SOURCE.read_text(encoding="utf-8")
        start = source.index("    def fetch_market_data_uncached(")
        end = source.index("    def ", start + 5)
        body = source[start:end]
        self.assertIn('if selected!="Dhan":',body)
        self.assertIn('V3 Dhan-only provider required',body)
        self.assertIn('Dhan-only market result unavailable',body)
        self.assertNotIn('Broker API not connected',body)
        self.assertNotIn('select Yahoo Finance',body)


if __name__ == "__main__":
    unittest.main()
