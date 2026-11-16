"""Offline five-filter readiness gates: real metrics are not automatically live signals."""
import unittest
from backend.dhan_option_metrics import calculate_option_metrics, OptionMetricsUnavailable


def chain(ce=100, pe=150):
    return {"status": "success", "data": {"oc": {
        "24900": {"ce": {"oi": ce}, "pe": {"oi": pe}},
        "25000": {"ce": {"oi": ce}, "pe": {"oi": pe}},
        "25100": {"ce": {"oi": ce}, "pe": {"oi": pe}},
    }}}


class FiveFilterOptionMetricContractTests(unittest.TestCase):
    def test_pcr_and_max_pain_are_calculated_but_not_promoted(self):
        metrics = calculate_option_metrics(chain())
        self.assertAlmostEqual(metrics["pcr"], 1.5)
        self.assertEqual(metrics["max_pain"], 25000)
        self.assertEqual(metrics["strike_count"], 3)
        self.assertEqual(metrics["freshness"], "unverified")
        self.assertIs(metrics["signal_eligible"], False)

    def test_missing_leg_or_invalid_oi_fails_closed(self):
        for invalid in (-1, float("nan"), None, True):
            with self.subTest(oi=repr(invalid)):
                with self.assertRaises(OptionMetricsUnavailable):
                    calculate_option_metrics(chain(ce=invalid))

    def test_incomplete_chain_fails_closed(self):
        with self.assertRaises(OptionMetricsUnavailable):
            calculate_option_metrics({"status": "success", "data": {"oc": {
                "25000": {"ce": {"oi": 100}, "pe": {"oi": 100}},
            }}})


if __name__ == "__main__":
    unittest.main()
