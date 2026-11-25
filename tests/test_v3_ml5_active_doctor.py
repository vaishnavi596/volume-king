import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from v3_smart_active_doctor import ml5_engine_observation

class ML5DoctorTests(unittest.TestCase):
    def test_empty_sources_do_not_vote(self):
        r=ml5_engine_observation(symbol="NIFTY",timeframe="1m",generation=1,
            history={},news={},futures={},options={},snapshot=None,now=1800000000,
            connected=True)
        self.assertEqual([x["box"] for x in r["boxes"]],list("TCNFO"))
        self.assertFalse(any(x["live_vote_eligible"] for x in r["boxes"]))
        self.assertEqual(r["combined"]["state"],"WAIT")
        self.assertEqual(r["comparison_status"],"UNVERIFIED")
        self.assertEqual(r["orders_sent"],0)
    def test_unsupported_frame_not_reused(self):
        r=ml5_engine_observation(symbol="NIFTY",timeframe="2m",generation=1,
            history={},news={},futures={},options={},snapshot=None,now=1800000000,
            connected=True)
        self.assertEqual(r["boxes"],[])
