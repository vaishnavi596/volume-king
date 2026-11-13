import unittest
from backend.dhan_option_metrics import calculate_option_metrics, OptionMetricsUnavailable


class DhanOptionMetricsTests(unittest.TestCase):
    def test_complete_chain_calculates_pcr_and_max_pain_but_never_votes(self):
        response={"status":"success","data":{"oc":{
            "100":{"ce":{"oi":100},"pe":{"oi":50}},
            "110":{"ce":{"oi":50},"pe":{"oi":100}},
            "120":{"ce":{"oi":50},"pe":{"oi":50}},
        }}}
        result=calculate_option_metrics(response)
        self.assertEqual(result["ce_oi"],200)
        self.assertEqual(result["pe_oi"],200)
        self.assertEqual(result["pcr"],1)
        self.assertEqual(result["max_pain"],110)
        self.assertFalse(result["signal_eligible"])
        self.assertEqual(result["freshness"],"unverified")

    def test_one_sided_or_oversized_chain_cannot_generate_metrics(self):
        for ce, pe in ((10, 0), (0, 10)):
            response={"status":"success","data":{"oc":{
                "100":{"ce":{"oi":ce},"pe":{"oi":pe}},
                "110":{"ce":{"oi":ce},"pe":{"oi":pe}},
            }}}
            with self.subTest(ce=ce, pe=pe):
                with self.assertRaises(OptionMetricsUnavailable):
                    calculate_option_metrics(response)
        oversized={"status":"success","data":{"oc":{
            str(i):{"ce":{"oi":1},"pe":{"oi":1}} for i in range(1,2002)
        }}}
        with self.assertRaises(OptionMetricsUnavailable):
            calculate_option_metrics(oversized)

    def test_missing_or_bad_leg_fails_closed(self):
        for bad in (None, {}, {"status":"failure"},
                    {"status":"success","data":{"oc":{"100":{"ce":{"oi":1},"pe":{"oi":1}}}}},
                    {"status":"success","data":{"oc":{"100":{"ce":{"oi":1},"pe":{"oi":1}},
                                                       "110":{"ce":{"oi":2},"pe":{}}}}}):
            with self.subTest(bad=bad):
                with self.assertRaises(OptionMetricsUnavailable):
                    calculate_option_metrics(bad)


if __name__=="__main__":
    unittest.main()
