"""Flat candle data cannot create fabricated momentum confirmation."""
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scanner_engine import analyze

class FlatMomentumVotes(unittest.TestCase):
    def test_flat_candles_have_neutral_rsi_and_supertrend(self):
        now=int(datetime.now(timezone.utc).timestamp())
        start=now-40*300
        bars=[[start+i*300,100,100,100,100,1000] for i in range(35)]
        result=analyze(bars,["RSI 14","Supertrend"],"5m")
        self.assertEqual(result["bias"],"WAIT")
        self.assertEqual({v["name"]:v["vote"] for v in result["votes"]},
                         {"RSI 14":0,"Supertrend":0})
        self.assertIn("RSI 50.0",result["votes"][0]["detail"])

if __name__=="__main__":
    unittest.main()
