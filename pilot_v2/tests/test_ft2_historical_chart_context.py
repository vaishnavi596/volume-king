"""V2 completed-candle chart and historical-only shortlist regression."""
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
SRC=Path(__file__).resolve().parents[1]/"android_app"/"src"
sys.path.insert(0,str(SRC))
from evidence_inbox import DeviceEvidenceInbox
from historical_chart_context import chart_points, historical_shortlist, choose_historical_shortlist_symbol


def bars(start=None, n=36):
    if start is None:
        start=int(datetime(2026,11,18,4,0,tzinfo=timezone.utc).timestamp())
    result=[]
    for i in range(n):
        close=101+i*.37
        result.append({"timestamp":start+180*i,"open":close-.2,
                       "high":close+1,"low":close-1,"close":close,
                       "volume":100+i,"completed":True})
    return result


class ChartContextTests(unittest.TestCase):
    def setUp(self):
        self.e=DeviceEvidenceInbox()

    def test_empty_and_unselected_never_display_chart(self):
        self.assertEqual(chart_points(self.e.candles,"TCS","3m",
                                      selected_equities=("TCS",)),())
        self.e.apply_candles("TCS","3m",1,bars(),
                             selected_equities=("TCS",),trusted_transport=True)
        self.assertEqual(chart_points(self.e.candles,"TCS","3m"),())
        self.assertEqual(len(chart_points(self.e.candles,"TCS","3m",
                                         selected_equities=("TCS",))),35)
        self.assertEqual(chart_points(self.e.candles,"TCS","1m",
                                      selected_equities=("TCS",)),())

    def test_shortlist_uses_real_local_indicators_not_five_filter_scores(self):
        self.e.apply_candles("TCS","3m",1,bars(),
                             selected_equities=("TCS","INFY"),
                             trusted_transport=True)
        out=historical_shortlist(self.e.candles,("TCS","INFY"))
        for row in out:
            self.assertIn("HIST",row["label"])
            self.assertIn("NOT verified Super Five",row["label"])
        self.assertEqual(self.e.filters.rows("TCS","3m",
                         selected_equities=("TCS","INFY"))[4][1],"WAIT")
        self.assertEqual(historical_shortlist(self.e.candles,("INFY",)),())

    def test_historical_shortlist_click_fails_closed_for_removed_or_missing(self):
        selected = ("TCS", "INFY")
        self.e.apply_candles("TCS", "3m", 1, bars(),
                             selected_equities=selected, trusted_transport=True)
        shortlist = historical_shortlist(self.e.candles, selected)
        if shortlist:
            pick = shortlist[0]["symbol"]
            self.assertEqual(choose_historical_shortlist_symbol(
                self.e.candles, selected, pick), pick)
        for bad in ("INFY", "NIFTY", "UNKNOWN", None):
            with self.subTest(symbol=bad), self.assertRaises(ValueError):
                choose_historical_shortlist_symbol(
                    self.e.candles, selected, bad, timeframe="3m")
        with self.assertRaises(ValueError):
            choose_historical_shortlist_symbol(
                self.e.candles, ("INFY",), "TCS")
        with self.assertRaises(ValueError):
            choose_historical_shortlist_symbol(
                self.e.candles, selected, "TCS", timeframe="1m")

    def test_replay_and_incomplete_data_do_not_erase_last_chart(self):
        self.e.apply_candles("NIFTY","1m",1,bars(),trusted_transport=True)
        before=chart_points(self.e.candles,"NIFTY","1m")
        self.assertFalse(self.e.apply_candles("NIFTY","1m",1,bars(),
                                              trusted_transport=True))
        with self.assertRaises(ValueError):
            self.e.apply_candles("NIFTY","1m",2,bars()[:-1]+[
                dict(bars()[-1],completed=False)],trusted_transport=True)
        self.assertEqual(chart_points(self.e.candles,"NIFTY","1m"),before)

    def test_flet_has_real_chart_and_source_safe_shortlist(self):
        source=(SRC/"main.py").read_text()
        self.assertIn("ft.LineChart(",source)
        self.assertIn("ft.LineChartDataPoint(",source)
        self.assertIn("chart_points(",source)
        self.assertIn("historical_shortlist(",source)
        self.assertIn("Super Five · verified signals WAIT",source)
        self.assertIn("select_historical_candidate(symbol)",source)
        self.assertIn('tooltip="Super Five Help"',source)
        self.assertNotIn("from server_feed import",source)

if __name__=="__main__":unittest.main()
