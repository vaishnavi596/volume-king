"""STANDARD-2 regular-session HIST suffix preservation contracts."""
import unittest
from datetime import datetime,timedelta,timezone
from historical_session_window import historical_regular_session_bars
from scanner_engine import analyze
IST=timezone(timedelta(hours=5,minutes=30))
def bar(h,m):
    t=int(datetime(2026,11,23,h,m,tzinfo=IST).timestamp())
    o=25000.0+m
    return [t,o,o+2,o-2,o+1,100]
class HistoricalSessionTests(unittest.TestCase):
    def test_remove_only_afterclose_suffix_without_mutating_source(self):
        rows=[bar(14,m) for m in range(50,60)]+[bar(15,m) for m in range(30)]+[bar(15,34)]
        original=[r[:] for r in rows]
        clean=historical_regular_session_bars(rows,"1m")
        self.assertEqual(len(clean),40)
        self.assertEqual(rows,original)
        self.assertEqual(analyze(rows,["EMA 9/21"],"1m")["votes"],[])
        self.assertTrue(analyze(clean,["EMA 9/21"],"1m")["votes"])
    def test_1856_same_day_suffix_is_not_intraday_gap(self):
        # B201 real phone: 15:29 IST followed by 18:56 IST zero-volume
        # gateway row must not block the 13 historical technical filters.
        rows=[bar(14,m) for m in range(50,60)]+[bar(15,m) for m in range(30)]
        final=bar(18,56);final[5]=0
        original=[x[:] for x in rows+[final]]
        result=historical_regular_session_bars(rows+[final],"1m")
        self.assertEqual(len(result),40)
        self.assertEqual(rows+[final],original)
        self.assertTrue(analyze(result,["EMA 9/21"],"1m")["votes"])
        self.assertFalse(analyze(rows+[final],["EMA 9/21"],"1m")["votes"])
    def test_invalid_afterclose_row_is_not_silently_removed(self):
        rows=[bar(14,m) for m in range(50,60)]+[bar(15,m) for m in range(30)]
        bad=bar(18,56);bad[2]=bad[1]-10
        result=historical_regular_session_bars(rows+[bad],"1m")
        self.assertEqual(len(result),41)
    def test_no_borrowing_previous_day(self):
        rows=[bar(14,m) for m in range(50,60)]+[bar(15,m) for m in range(30)]
        tomorrow=bar(18,56);tomorrow[0]+=86400
        input_rows=rows+[tomorrow]
        self.assertIs(historical_regular_session_bars(input_rows,"1m"),input_rows)
    def test_interior_gap_still_waits(self):
        rows=[bar(14,m) for m in range(20,50) if m!=42]+[bar(15,m) for m in range(15)]+[bar(15,34)]
        clean=historical_regular_session_bars(rows,"1m")
        self.assertEqual(analyze(clean,["EMA 9/21"],"1m")["votes"],[])
    def test_unknown_timeframe_or_short_series_not_trimmed(self):
        rows=[bar(15,m) for m in range(20,30)]+[bar(15,34)]
        self.assertIs(historical_regular_session_bars(rows,"1m"),rows)
        rows=[bar(15,m) for m in range(30)]+[bar(15,34)]
        self.assertIs(historical_regular_session_bars(rows,"2m"),rows)
if __name__=="__main__":unittest.main()
