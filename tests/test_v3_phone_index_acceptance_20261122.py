import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "ops/v3_phone_index_acceptance_20261122.py"
spec = importlib.util.spec_from_file_location("v3_phone_acceptance", MODULE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PhoneIndexAcceptance(unittest.TestCase):
    def test_missing_data_never_passes(self):
        result = module.assess({})
        self.assertEqual(result["overall"], "INCOMPLETE")
        self.assertEqual(result["provider_source"], "NOT_VERIFIED")

    def test_three_prices_are_not_freshness_proof(self):
        result = module.assess({"quotes": {
            "NIFTY": {"ltp": 26000},
            "BANKNIFTY": {"ltp": 61000},
            "SENSEX": {"ltp": 85000}}})
        self.assertEqual(result["overall"], "PRICES_PRESENT_ONLY")
        self.assertEqual(result["freshness"], "NOT_VERIFIED")

    def test_provider_quota_classification_requires_exact_stage(self):
        self.assertEqual(module.assess({"429_stage": "PROVIDER_QUOTA"})["429_stage"],
                         "PROVIDER_QUOTA")
        self.assertEqual(module.assess({"index_failure_code": "GATEWAY_HTTP_429"})["429_stage"],
                         "NOT_CONFIRMED")

    def test_invalid_price_and_payload_rejected(self):
        self.assertEqual(module.assess({"quotes": {"SENSEX": {"ltp": True}}})["overall"],
                         "INCOMPLETE")
        with self.assertRaises(ValueError):
            module.assess([])


if __name__ == "__main__":
    unittest.main()
