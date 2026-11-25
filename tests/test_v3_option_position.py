import unittest
from v3_option_position import historical_option_position

class HistoricalOptionPositionTests(unittest.TestCase):
    def fixture(self):
        rows=[{"strike":i,"ce":{"oi":10},"pe":{"oi":20}} for i in range(100,107)]
        return {"source":"dhan","symbol":"TCS","expiry":"2099-12-31",
                "freshness":"unverified","signal_eligible":False,
                "atm_window":{"source":"dhan","freshness":"unverified",
                "signal_eligible":False,"atm":103,"rows":rows}}
    def run_position(self,data,symbol="TCS",expiry="2099-12-31"):
        return historical_option_position(data,symbol=symbol,expiry=expiry,now=1795600000)
    def test_position_context_never_live_vote(self):
        result=self.run_position(self.fixture())
        self.assertEqual(result["position"],"PUT_OI_HEAVY")
        self.assertFalse(result["live_vote_eligible"])
    def test_wrong_identity_rejected(self):
        self.assertFalse(self.run_position(self.fixture(),symbol="NIFTY")["available"])
        self.assertFalse(self.run_position(self.fixture(),expiry="2099-12-30")["available"])
    def test_missing_leg_rejected(self):
        data=self.fixture()
        del data["atm_window"]["rows"][0]["ce"]
        self.assertEqual(self.run_position(data)["code"],"BK-OPT-002")

    def test_summary_label_discloses_expiry_and_abstention(self):
        from v3_option_position import option_position_label
        label=option_position_label(self.run_position(self.fixture()))
        self.assertIn("HIST PUT OI HEAVY",label)
        self.assertIn("2099-12-31",label)
        self.assertIn("WAIT",label)
        self.assertIn("not LIVE",label)
        self.assertEqual(option_position_label({"available":False}),"")
