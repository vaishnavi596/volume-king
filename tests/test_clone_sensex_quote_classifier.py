"""Offline tests for redacted SENSEX quote classifier."""
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / "scripts" / "classify_clone_sensex_quote_readonly.py"
spec = importlib.util.spec_from_file_location("sensex_classifier", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SensexQuoteClassifierTests(unittest.TestCase):
    def test_partial_gateway_quote(self):
        data = {"quotes": {"NIFTY": {"ltp": 25800.60},
                           "BANKNIFTY": {"ltp": 64635.20}},
                "unavailable": ["SENSEX"]}
        got = module.classify(data)
        self.assertEqual(got["indices"]["SENSEX"], "PROVIDER_UNAVAILABLE_OR_REJECTED")
        self.assertFalse(got["provider_root_cause_proven"])

    def test_missing_sensex_security_id_in_idx_segment(self):
        got = module.classify({"status": "success", "data": {
            "IDX_I": {"13": {"last_price": 25800.60},
                      "25": {"last_price": 64635.20}}}})
        self.assertEqual(got["indices"]["SENSEX"], "SECURITY_ID_MISSING")

    def test_invalid_price_does_not_turn_live(self):
        got = module.classify({"status": "success", "data": {
            "IDX_I": {"51": {"last_price": 0}}}})
        self.assertEqual(got["indices"]["SENSEX"], "INVALID_LAST_PRICE")
        self.assertFalse(got["provider_root_cause_proven"])


if __name__ == "__main__":
    unittest.main()
