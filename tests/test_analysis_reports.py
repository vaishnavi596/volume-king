import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from analysis_reports import AnalysisAudit, complete_filter_rows
from scanner_engine import DEFAULT_FILTERS
from server_feed import DHAN_VERIFIED_SYMBOLS



class AnalysisReportsTests(unittest.TestCase):

    def test_all_54_symbols_have_a_row_for_every_selected_filter_on_missing_data(self):
        assert len(DHAN_VERIFIED_SYMBOLS) == 54
        for symbol in DHAN_VERIFIED_SYMBOLS:
            rows = complete_filter_rows({"reason": "Need 30 completed candles"}, DEFAULT_FILTERS)
            assert [r["name"] for r in rows] == DEFAULT_FILTERS
            assert all(r["vote"] is None for r in rows)
            assert all("30" in r["detail"] for r in rows)


    def test_missing_votes_never_become_neutral_and_chart_only_does_not_vote(self):
        raw = {"votes": [{"name": "MACD", "vote": 1, "detail": "Cross"}]}
        rows = complete_filter_rows(raw, ["MACD", "RSI 14", "EMA 9/21"], {"EMA 9/21": "Chart"})
        assert [r["vote"] for r in rows] == [1, None, None]
        assert "Chart only" in rows[-1]["detail"]
        rows[0]["vote"] = -1
        assert raw["votes"][0]["vote"] == 1


    def test_coverage_counts_symbols_not_timeframes_and_invalidates_on_settings_change(self):
        audit = AnalysisAudit()
        audit.reset(("Dhan", "settings-v1"))
        audit.record("TCS", "5m", result={"timestamp": 100, "votes": [{"vote": 1}]})
        audit.record("INFY", "5m", stage="candle fetch", error="FeedError")
        audit.record("NIFTY", "5m", result={"reason": "Need 30 candles"})
        audit.record("TCS", "1m", stage="candle fetch", error="FeedError")
        rows, counts = audit.coverage(["TCS", "INFY", "NIFTY", "SENSEX", "TCS"])
        assert counts == {"ANALYZED": 1, "INSUFFICIENT": 1, "ERROR": 1, "PENDING": 1}
        rows[0]["status"] = "ERROR"
        assert audit.coverage(["TCS"])[1]["ANALYZED"] == 1
        audit.reset(("Dhan", "settings-v2"))
        assert audit.coverage(DHAN_VERIFIED_SYMBOLS)[1]["PENDING"] == 54
