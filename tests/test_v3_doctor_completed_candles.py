"""B178 Doctor HIST must reuse the completed, exact-frame Dhan candle gate."""
from pathlib import Path
import unittest
from five_engine import completed_timeframe_candle_balance


class DoctorCompletedCandleTests(unittest.TestCase):
    def test_doctor_source_reuses_exact_completed_gate(self):
        source=(Path(__file__).resolve().parents[1] / "src" / "main.py").read_text()
        start=source.index('elif not ready and name=="candle":')
        end=source.index('if name=="candle":',start)
        block=source[start:end]
        self.assertIn('completed_timeframe_candle_balance(',block)
        self.assertIn('history,tf,now=time.time()',block)
        self.assertNotIn('historical_candle_balance(bars)',block)

    def test_current_forming_bar_cannot_inflate_hist(self):
        # Eight completed bullish bodies plus one forming bearish body:
        # only the eight completed bodies may be used.
        start=1795412400
        bars=[[start+i*60,100+i,102+i,99+i,101+i,100]
              for i in range(8)]
        bars.append([start+8*60,110,111,107,108,0])
        history={"source":"Dhan","_scanner_timeframe":"1m","bars":bars}
        result=completed_timeframe_candle_balance(
            history,"1m",now=start+8*60+20)
        self.assertIsNotNone(result)
        self.assertEqual(result["bullish"],100)
        self.assertEqual(result["bearish"],0)
        self.assertFalse(result["verified"])

    def test_mismatch_timeframe_rejected(self):
        start=1795412400
        bars=[[start+i*60,100+i,102+i,99+i,101+i,100]
              for i in range(9)]
        history={"source":"Dhan","_scanner_timeframe":"1m","bars":bars}
        self.assertIsNone(completed_timeframe_candle_balance(
            history,"3m",now=start+600))


if __name__=="__main__":
    unittest.main()
