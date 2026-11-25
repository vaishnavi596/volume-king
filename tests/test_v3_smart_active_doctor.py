import unittest
from v3_smart_active_doctor import active_report

class SmartActiveDoctorTests(unittest.TestCase):
    def test_healthy_hidden_and_regressions_reappear(self):
        args=dict(generation=1,symbols=["TCS","INFY"],quote_present=["TCS","INFY"],
                  index_present=["NIFTY","BANKNIFTY","SENSEX"],
                  connected={"Dhan":True,"Oracle":True},signal_present=["TCS","INFY"],
                  attempts={"TCS":10,"INFY":20},now_monotonic=50,market_open=True,
                  errors=[],progress={},performance={},quote_attempt_age=5)
        report=active_report(**args)
        self.assertEqual(report["healthy_hidden_count"],6)
        self.assertFalse(report["source_live_verified"])
        self.assertEqual(report["provider_requests"],0)
        self.assertEqual(report["orders_sent"],0)
        self.assertEqual(report["active"][0]["oldest_attempt_symbols"],["TCS","INFY"])
        args["quote_present"]=["TCS"]
        args["errors"]=["index"]
        report=active_report(**args)
        self.assertEqual(report["healthy_hidden_count"],4)
        self.assertIn("EQUITY_QUOTE_COVERAGE",[r["check"] for r in report["active"]])
        self.assertIn("OBSERVED_ERRORS",[r["check"] for r in report["active"]])
        self.assertIn("FULL_FUNCTIONAL_WIRING",[r["check"] for r in report["active"]])
