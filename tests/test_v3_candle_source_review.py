"""B178 source-quality review: repeated OHLCV and late candles are review-only."""
import ast
import pathlib
import sys
import unittest
from datetime import datetime,timezone,timedelta
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from v3_candle_source_review import inspect_candle_tail
IST=timezone(timedelta(hours=5,minutes=30))
def ts(hour,minute):return datetime(2026,11,23,hour,minute,tzinfo=IST).timestamp()
def candle(t,price=25366.4,volume=916):
    return [t,price,price,price,price,volume]

class ReviewTests(unittest.TestCase):
    def test_user_report_duplicate_seven_and_late_one(self):
        bars=[candle(ts(15,23+i)) for i in range(7)]
        bars.append(candle(ts(19,57),25349.65,0))
        original=[v[:] for v in bars]
        r=inspect_candle_tail(bars)
        codes={x["code"] for x in r["review"]}
        self.assertEqual(codes,{"REPEATED_IDENTICAL_OHLCV_REVIEW",
                                "OUTSIDE_REGULAR_SESSION_CANDLE_PRESENT"})
        self.assertFalse(r["source_error_confirmed"])
        self.assertEqual(r["provider_requests"],0)
        self.assertEqual(r["orders_sent"],0)
        self.assertEqual(bars,original)
    def test_normal_completed_candles_hidden(self):
        bars=[candle(ts(15,15+i),25360+i,500+i) for i in range(8)]
        r=inspect_candle_tail(bars)
        self.assertEqual(r["review"],[])
        self.assertEqual(r["status"],"NO_REVIEW_FLAGS")
    def test_one_doji_does_not_imply_corrupted_data(self):
        bars=[candle(ts(15,15),25350)]+[
            candle(ts(15,16+i),25351+i,900+i) for i in range(7)]
        self.assertEqual(inspect_candle_tail(bars)["review"],[])
    def test_wrong_interval_has_no_fake_run(self):
        bars=[candle(ts(15,20+i)) for i in range(8)]
        r=inspect_candle_tail(bars,timeframe="3m")
        self.assertNotIn("REPEATED_IDENTICAL_OHLCV_REVIEW",
                         {x["code"] for x in r["review"]})
    def test_doctor_is_instrumented_read_only(self):
        content=(ROOT/"src/main.py").read_text()
        ast.parse(content)
        self.assertIn('diagnostic_context["source_quality_review"]=inspect_candle_tail(',content)
        self.assertIn("source_quality_review",content)

if __name__=="__main__": unittest.main()
