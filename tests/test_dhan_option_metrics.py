import unittest
from backend.dhan_option_metrics import calculate_option_metrics, listed_atm_window, OptionMetricsUnavailable


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


    def test_listed_atm_window_uses_only_broker_listed_strikes_and_never_votes(self):
        raw={"status":"success","data":{"oc":{
            str(strike):{"ce":{"oi":100,"volume":20,"last_price":4.5},
                         "pe":{"oi":80,"volume":30,"last_price":3.5}}
            for strike in (80,90,100,110,120,130,140,150,160)
        }}}
        window=listed_atm_window(raw,spot=121)
        self.assertEqual(window["atm"],120)
        self.assertEqual([r["strike"] for r in window["rows"]],[90,100,110,120,130,140,150])
        self.assertEqual(window["rows"][3]["ce"]["volume"],20.0)
        self.assertEqual(window["rows"][3]["pe"]["last_price"],3.5)
        self.assertEqual(window["source"],"dhan")
        self.assertEqual(window["freshness"],"unverified")
        self.assertIs(window["signal_eligible"],False)

    def test_listed_atm_window_rejects_invalid_spot_and_boundary_window(self):
        raw={"status":"success","data":{"oc":{
            str(strike):{"ce":{"oi":10},"pe":{"oi":10}}
            for strike in (80,90,100,110,120,130,140)
        }}}
        for spot in (None,0,float("nan"),float("inf"),True):
            with self.subTest(spot=spot), self.assertRaises(OptionMetricsUnavailable):
                listed_atm_window(raw,spot=spot)
        with self.assertRaises(OptionMetricsUnavailable):
            listed_atm_window(raw,spot=80)
        with self.assertRaises(OptionMetricsUnavailable):
            listed_atm_window(raw,spot=140)


    def test_atm_window_requires_all_seven_broker_listed_contracts(self):
        def chain(strikes):
            return {"status": "success", "data": {"oc": {
                str(k): {"ce": {"oi": 120}, "pe": {"oi": 95}}
                for k in strikes
            }}}
        # A seven-row chain is not sufficient when ATM lacks three strikes
        # on each side. Never synthesize missing or unlisted strikes.
        for strikes, spot in (
            ((100, 110, 120, 130, 140, 150, 160), 100),
            ((100, 110, 120, 130, 140, 150, 160), 160),
            ((100, 110, 120, 130, 140, 150), 130),
        ):
            with self.subTest(strikes=strikes, spot=spot):
                with self.assertRaises(OptionMetricsUnavailable):
                    listed_atm_window(chain(strikes), spot=spot)

    def test_atm_window_invalid_oi_and_optional_fields_fail_closed(self):
        strikes = tuple(range(80, 171, 10))
        for side, field, value in (
            ("ce", "oi", None), ("pe", "oi", -1),
            ("ce", "oi", float("nan")), ("pe", "oi", True),
            ("ce", "volume", -1), ("pe", "last_price", float("inf")),
            ("ce", "previous_oi", "100"),
        ):
            with self.subTest(side=side, field=field, value=str(value)):
                response = {"status": "success", "data": {"oc": {
                    str(k): {"ce": {"oi": 100}, "pe": {"oi": 90}}
                    for k in strikes
                }}}
                response["data"]["oc"]["120"][side][field] = value
                with self.assertRaises(OptionMetricsUnavailable):
                    listed_atm_window(response, spot=120)

    def test_atm_window_never_promotes_broker_envelope_to_fresh_signal(self):
        response = {"status": "success", "data": {"oc": {
            str(k): {"ce": {"oi": 100, "previous_oi": 80},
                     "pe": {"oi": 120, "previous_oi": 100}}
            for k in range(80, 171, 10)
        }}, "freshness": "exchange_verified", "signal_eligible": True}
        window = listed_atm_window(response, spot=120)
        self.assertEqual(len(window["rows"]), 7)
        self.assertEqual(window["freshness"], "unverified")
        self.assertIs(window["signal_eligible"], False)
        self.assertEqual(window["source"], "dhan")
        self.assertEqual(window["rows"][3]["ce"]["previous_oi"], 80.0)



if __name__=="__main__":
    unittest.main()
