"""Missing a single candle inside a session must suppress scanner signals."""
import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scanner_engine import analyze

IST=timezone(timedelta(hours=5,minutes=30))

class MissingCandleGuard(unittest.TestCase):
    def test_one_missing_five_minute_candle_fails_closed(self):
        start=datetime(2026,11,12,10,0,tzinfo=IST).timestamp()
        bars=[[start+i*300,100,101,99,100,1000] for i in range(40)]
        bars.pop(18)
        result=analyze(bars,["EMA 9/21"],"5m")
        self.assertEqual(result["bias"],"WAIT")
        self.assertEqual(result["votes"],[])
        self.assertEqual(result["reason"],"Missing candles within trading session")

    def test_continuous_candles_not_rejected_as_missing(self):
        start=datetime(2026,11,12,10,0,tzinfo=IST).timestamp()
        bars=[[start+i*300,100,101,99,100,1000] for i in range(40)]
        result=analyze(bars,["EMA 9/21"],"5m")
        self.assertNotEqual(result["reason"],"Missing candles within trading session")

if __name__=="__main__":
    unittest.main()
